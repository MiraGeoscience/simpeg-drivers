#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from SimPEG.data import Data
from SimPEG.data_misfit import L2DataMisfit
from SimPEG.maps import IdentityMap, TileMap

from simpeg_drivers.utils.utils import create_nested_mesh

if TYPE_CHECKING:
    from SimPEG.simulation import BaseSimulation
    from SimPEG.survey import BaseRx, BaseSrc, BaseSurvey

    from simpeg_drivers.driver import InversionDriver


class SimPEGSimulation(ABC):
    _class_type: type[BaseSimulation]

    n_blocks: int = 1
    padding_cells: int = 6

    def __init__(self, driver, survey: BaseSurvey, uid: int, nested: bool = False):
        self.driver = driver
        self.survey = survey
        self.uid = uid
        self.global_map = None

        if nested:
            self.create_tiled_inputs()
            self.uid = uid
        else:
            self.mesh = self.driver.inversion_mesh.mesh
            self.active_cells = self.driver.models.active_cells
            self.global_map = IdentityMap(nP=self.n_values)

    @abstractmethod
    def build(self) -> BaseSimulation:
        """
        Form the SimPEG simulation object.
        """

    def _get_sensitivity_path(self) -> str:
        """Build path to destination of on-disk sensitivities."""
        out_dir = Path(self.driver.params.workpath) / "SimPEG_Inversion"

        if self.uid is None:
            sens_path = out_dir / "Tile.zarr"
        else:
            sens_path = out_dir / f"Tile{self.uid}.zarr"

        return str(sens_path)

    @property
    def n_values(self):
        """Return the number of active values in the model."""
        return int(self.n_blocks * self.active_cells.sum())

    def create_tiled_inputs(self):
        self.mesh = create_nested_mesh(
            self.survey,
            self.driver.inversion_mesh.mesh,
            minimum_level=3,
            padding_cells=self.padding_cells,
        )
        self.global_map = TileMap(
            self.driver.inversion_mesh.mesh,
            self.driver.models.active_cells,
            self.mesh,
            enforce_active=True,
            components=self.n_blocks,
        )
        self.active_cells = self.global_map.local_active


class SimPEGSurvey(ABC):
    _class_type: type[BaseSurvey]
    _receiver_type: type[BaseRx]
    _source_type: type[BaseSrc]

    @classmethod
    @abstractmethod
    def build(cls, driver: InversionDriver, local_index: np.ndarray | tuple, **_):
        """Generate a concrete SimPEG survey from input."""

    @classmethod
    @abstractmethod
    def create_receivers(
        cls, driver: InversionDriver, local_index: np.ndarray | tuple, **_
    ):
        """Generate a concrete SimPEG survey from input."""

    @classmethod
    @abstractmethod
    def create_sources(cls, driver: InversionDriver, receiver_class: BaseRx, **_):
        """Generate a concrete SimPEG survey from input."""


class SimPEGMisfit(ABC):
    _class_type = L2DataMisfit
    _simulation_factory: type[SimPEGSimulation]
    _survey_factory: type[SimPEGSurvey]
    ordering: np.ndarray | None = None
    dummy = -999.0

    def __init__(self, driver, indices: np.ndarray | tuple | None = None, uid: int = 0):
        self._nested = True
        self.driver = driver
        self.indices = indices
        self.uid = uid

    def build(self) -> L2DataMisfit:
        simulation_class = self._simulation_factory(
            self.driver,
            self.survey,
            self.uid,
            nested=self._nested,
        )

        simulation = simulation_class.build()
        simulation.survey = self.survey
        simulation.workers = self.driver.params.distributed_workers

        local_misfit = self._class_type(
            self.data, simulation, model_map=simulation_class.global_map
        )
        return local_misfit

    @abstractmethod
    def _get_data(self):
        """Add data to survey object."""

    def _stack_channels(self, channel_data: dict[str, np.ndarray], mode: str):
        """
        Convert dictionary of data/uncertainties to stacked array.

        parameters:
        ----------

        channel_data: Array of data to stack
        mode: Stacks rows or columns before flattening. Must be either 'row' or 'column'.


        notes:
        ------
        If mode is row the components will be clustered in the resulting 1D array.
        Column stacking results in the locations being clustered.

        """
        if mode == "column":
            return np.column_stack(list(channel_data.values())).ravel()

        return np.row_stack(list(channel_data.values())).ravel()

    @property
    def data(self):
        """Return the data and uncertainties for the misfit calculation."""
        if not self.driver.params.forward_only:
            observed, uncertainties = self._get_data()
        else:
            observed, uncertainties = None, None

        return Data(self.survey, dobs=observed, standard_deviation=uncertainties)

    @property
    def indices(self) -> np.ndarray | tuple:
        """
        Indices of data to use in the misfit calculation.
        """
        return self._indices

    @indices.setter
    def indices(self, value):
        if value is None:
            self._indices = np.arange(self.driver.inversion_data.locations.shape[0])
            self._nested = False
        else:
            self._indices = np.array(value, dtype=int)

    @property
    def survey(self):
        """
        Survey object.
        """
        return self._survey_factory.build(self.driver, self.indices)
