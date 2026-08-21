# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=too-many-lines
# flake8: noqa

from __future__ import annotations

from io import BytesIO
from abc import abstractmethod, ABC
from typing import Self
from copy import deepcopy
import sys
from datetime import datetime, timedelta
import logging
from pathlib import Path
from time import time

import numpy as np
from pandas import read_csv
from dask.distributed import get_client, Client

from geoapps_utils.base import Driver, Options

from geoapps_utils.utils.importing import GeoAppsError

from geoh5py import Workspace
from geoh5py.data import FilenameData
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import DrapeModel, FEMSurvey, Octree
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import UIJson

from simpeg import (
    directives,
    inverse_problem,
    inversion,
    maps,
    objective_function,
    optimization,
    simulation,
)
from simpeg.electromagnetics.frequency_domain.simulation_1d import Simulation1DLayered

from simpeg.regularization import (
    BaseRegularization,
    RegularizationMesh,
    Sparse,
    SparseSmoothness,
)

from simpeg_drivers import __version__
from simpeg_drivers.components import (
    InversionData,
    InversionMesh,
    InversionModelCollection,
    InversionTopography,
)
from simpeg_drivers.components.factories import (
    DirectivesFactory,
    MisfitFactory,
    SimulationFactory,
)
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
)
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.uijson import SimPEGDriversUIJson
from simpeg_drivers.utils.nested import tile_locations
from simpeg_drivers.utils.regularization import cell_neighbors, set_rotated_operators
from simpeg_drivers.utils.utils import (
    argument_parser,
    driver_class_from_dict,
    start_dask_run,
)

mlogger = logging.getLogger("distributed")
mlogger.setLevel(logging.WARNING)


class BaseDriver(Driver, ABC):
    """
    Base class for drivers handling the parallel setup.
    """

    def __init__(
        self,
        params: Options,
        client: Client | bool | None = None,
        workers: list[str] | None = None,
        logger: logging.Logger | None | bool = None,
    ):
        super().__init__(params)

        self.inversion_type = self.params.inversion_type
        self._data_misfit: objective_function.ComboObjectiveFunction | None = None
        self._directives: list[directives.InversionDirective] | None = None
        self._inverse_problem: inverse_problem.BaseInvProblem | None = None
        self._inversion_data: InversionData | None = None
        self._inversion_mesh: InversionMesh | None = None
        self._inversion_topography: InversionTopography | None = None
        self.logger: InversionLogger | None = logger
        self._mapping: list[maps.IdentityMap] | None = None
        self._models: InversionModelCollection | None = None
        self._n_values: int | None = None
        self._simulation: simulation.BaseSimulation | None = None
        self._ordering: list[np.ndarray] | None = None
        self._mappings: list[maps.IdentityMap] | None = None
        self.tiles: dict[str, list[np.ndarray]]

        self.out_group = self.validate_out_group(self.params.out_group)
        self._client: Client | bool = validate_client(client)

        if getattr(self.params, "store_sensitivities", None) == "disk" and self.client:
            raise GeoAppsError(
                "Disk storage of sensitivities is not compatible with distributed processing."
            )

        self._workers: list[tuple[str]] = validate_workers(self._client, workers)

    @property
    def client(self) -> Client | bool | None:
        """
        Dask client or False if not using Dask.distributed.
        """
        return self._client

    @property
    def data_misfit(self):
        """The Simpeg.data_misfit class"""
        if getattr(self, "_data_misfit", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                if self.logger and self.params.compute.tile_spatial > 1:
                    self.logger.write(
                        f"Setting up {self.params.compute.tile_spatial} tiles . . .\n"
                    )
                # Tile locations
                self.tiles = self.get_tiles()

                self._data_misfit = MisfitFactory(
                    self.params,
                    self.simulation,
                    client=self.client,
                    workers=self.workers,
                ).build(self.tiles)

        return self._data_misfit

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._directives = DirectivesFactory(self)
        return self._directives

    def get_nested_tiles(self) -> list:
        """
        Get nested tiles per channel and receiver tiling.

        Returns a flat list of tiles if auto_scale_channels is False,
        otherwise returns a nested list [channel][tiles].
        """
        nested_tiles = []
        for channel in self.tiles.values():
            tile_list = []
            for tile in channel:
                if self.params.directives.auto_scale_tiles:
                    tile_list.append(tile)
                else:
                    tile_list += tile

            if self.params.directives.auto_scale_channels:
                nested_tiles.append(tile_list)
            else:
                nested_tiles += tile_list

        return nested_tiles

    def get_tiles(self) -> dict[str, list[np.ndarray]]:
        """
        Parse the data locations into tiles for distributed processing.

        Adapts differently to the inversion type (1D, 2D or 3D).

        :return: Dictionary with channels as keys and list of tiles as values.
        """
        tiles = tile_locations(
            self.inversion_data.locations,
            self.params.compute.tile_spatial,
            labels=self.inversion_data.parts,
            sorting=self.simulation.survey.sorting,
        )
        tiles = self.split_list(tiles)

        # Base slice over frequencies
        if self.params.inversion_type in [
            "apparent conductivity",
            "magnetotellurics",
            "tipper",
            "fdem",
        ]:
            channels = self.simulation.survey.frequencies
        else:
            channels = [None]

        # Duplicate tiles for each channel
        return {channel: tiles for channel in channels}

    @property
    def inversion_data(self) -> InversionData:
        """Inversion data"""
        if getattr(self, "_inversion_data", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._inversion_data = InversionData(self.workspace, self.params)

        return self._inversion_data

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._inversion_mesh = InversionMesh(self.workspace, self.params)
        return self._inversion_mesh

    @property
    def inversion_topography(self):
        """Inversion topography"""
        if getattr(self, "_inversion_topography", None) is None:
            self._inversion_topography = InversionTopography(
                self.workspace, self.params
            )
        return self._inversion_topography

    @property
    def inverse_problem(self):
        if getattr(self, "_inverse_problem", None) is None:
            self._inverse_problem = inverse_problem.BaseInvProblem(
                self.data_misfit,
                self.regularization,
                self.optimization,
            )

            if (
                not self.params.forward_only
                and self.params.cooling_schedule.initial_beta
            ):
                self._inverse_problem.beta = self.params.cooling_schedule.initial_beta

        return self._inverse_problem

    @property
    def logger(self) -> InversionLogger | None:
        """
        Inversion logger
        """
        return self._logger

    @logger.setter
    def logger(self, value: InversionLogger | None | bool):
        if value is True or value is None:
            self._logger = InversionLogger(self)
        elif value is False:
            self._logger = None
        elif isinstance(value, logging.Logger):
            self._logger = value
        else:
            raise TypeError(
                "Logger must be a InversionLogger instance, None, True or False."
            )

    @property
    def mapping(self) -> list[maps.Projection] | None:
        """Model mapping for the inversion."""
        if self._mapping is None:
            mapping = []
            start = 0
            n_blocks = 3 if self.models.is_vector else 1

            for _ in range(n_blocks):
                mapping.append(
                    maps.Projection(
                        self.n_values * n_blocks, slice(start, start + self.n_values)
                    )
                )
                start += self.n_values

            self._mapping = mapping

        return self._mapping

    @mapping.setter
    def mapping(self, value: maps.IdentityMap | list[maps.IdentityMap]):
        if not isinstance(value, list):
            value = [value]

        if not all(
            isinstance(val, maps.IdentityMap) and val.shape[0] == self.n_values
            for val in value
        ):
            raise TypeError(
                "'mapping' must be an instance of maps.IdentityMap with shape (n_values, *). "
                f"Provided {value}"
            )

        self._mapping = value

    @property
    def models(self):
        """Inversion models"""
        if getattr(self, "_models", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._models = InversionModelCollection(self)

        return self._models

    @property
    def n_blocks(self):
        """
        Number of model components in the inversion.
        """
        return 3 if "magnetic vector" in self.params.inversion_type else 1

    @property
    def n_values(self):
        """Number of values in the model"""
        if self._n_values is None:
            self._n_values = self.models.n_active

        return self._n_values

    def split_list(self, tiles: list[np.ndarray]) -> list[list[np.ndarray]]:
        """
        Number of splits for the data misfit to be distributed evenly among workers.
        """
        if not self.workers:
            return [[tile] for tile in tiles]

        n_tiles = len(tiles)

        n_channels = 1
        if isinstance(self.params.data_object, FEMSurvey) and not isinstance(
            self.simulation, Simulation1DLayered
        ):
            n_channels = len(self.params.data_object.channels)

        split_list = [1] * n_tiles

        count = 0
        while (np.sum(split_list) * n_channels) % len(self.workers) != 0:
            split_list[count % n_tiles] += 1
            count += 1

        if self.logger:
            self.logger.write(
                f"Number of misfits: {np.sum(split_list)} distributed over {len(self.workers)} workers.\n"
            )

        flat_tile_list = []
        for tile, split in zip(tiles, split_list):
            flat_tile_list.append(
                [sub for sub in np.array_split(tile, split) if len(sub) > 0]
            )

        return flat_tile_list

    @property
    def ordering(self):
        """List of ordering of the data."""
        return self.inversion_data.survey.ordering

    @property
    def out_group(self) -> SimPEGGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    @out_group.setter
    def out_group(self, value: SimPEGGroup):
        self._out_group = self.validate_out_group(value)
        self.params.out_group = self._out_group

    @property
    def params(self) -> BaseForwardOptions | BaseInversionOptions:
        """Application parameters."""
        return self._params

    @params.setter
    def params(
        self,
        val: BaseForwardOptions | BaseInversionOptions,
    ):
        if not isinstance(
            val,
            (
                BaseForwardOptions,
                BaseInversionOptions,
                BaseJointOptions,
            ),
        ):
            raise TypeError(
                "Parameters must be of type 'BaseInversionOptions', 'BaseForwardOptions' or 'BaseJointOptions'."
            )
        self._params = val

    @property
    def regularization(self):
        """
        Base regularization for the inversion.

        Returns a BaseRegularization if forward_only is True, otherwise returns a ComboObjectiveFunction.
        """

        return objective_function.ComboObjectiveFunction()

    @property
    def optimization(self):
        """
        Base optimization for the inversion.
        """
        return optimization.ProjectedGNCG()

    @property
    def simulation(self):
        """
        The simulation object used in the inversion.
        """
        if getattr(self, "_simulation", None) is None:
            simulation_factory = SimulationFactory(self.params)
            self._simulation = simulation_factory.build(
                mesh=self.inversion_mesh.mesh,
                models=self.models,
                survey=self.inversion_data.survey,
            )

            if not hasattr(self._simulation, "active_cells"):
                self._simulation.active_cells = self.models.active_cells

        return self._simulation

    @abstractmethod
    def simpeg_run(self):
        """
        Run call to simpeg.
        """

    @abstractmethod
    def start_message(self):
        """
        Starting message displayed by the logger.
        """

    def run(self, start_iteration: int = -1):
        """
        Run inversion from params

        :param start_iteration: Whether to warm-start the inversion.
        """

        if self.logger:
            sys.stdout = self.logger

        with fetch_active_workspace(self.workspace, mode="r+"):
            try:
                if any(
                    [
                        child
                        for child in self.out_group.children
                        if child.name.endswith(".out")
                    ]
                ):
                    self.warm_start(start_iteration)
                else:
                    self.params.ui_json.to_file_data(self.out_group)

                    if self.logger:
                        self.logger.start()

                    self.start_message()

                self.simpeg_run()

            except np.core._exceptions._ArrayMemoryError as error:  # pylint: disable=protected-access
                raise GeoAppsError(
                    "Memory Error: Sensitivities too large for system. \n"
                    "Try reducing the number of data, reducing the number of cells in the mesh\n"
                    "or increase the number of tiles."
                ) from error

        if self.logger:
            self.logger.end()
            sys.stdout = self.logger.terminal

        if self.directives.save_iteration_log_files:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self.directives.save_iteration_log_files.write(1)

    @classmethod
    def start(
        cls,
        filepath: str | Path | UIJson,
        mode="r+",
        start_iteration: int = -1,
        **kwargs,
    ) -> Self:
        """
        Run application specified by 'filepath' ui.json file.

        :param filepath: Path to valid ui.json file for the application driver.
        :param mode: Mode to open the geoh5 file with.
        :param start_iteration: Iteration to warm-start the inversion if possible. Defaults to last iteration (-1).
        :param kwargs: Additional keyword arguments for Options class.

        :return: Self object.
        """

        uijson = (
            SimPEGDriversUIJson.read(filepath)
            if isinstance(filepath, str | Path)
            else filepath
        )

        if not isinstance(uijson, UIJson):
            raise TypeError("Input file must be a string path or a UIJson object.")

        if uijson.geoh5 is None:
            raise GeoAppsError("The application needs a valid 'geoh5' file.")

        with Workspace(uijson.geoh5, mode=mode) as workspace:
            try:
                data = uijson.to_params(workspace)
                kwargs.update(data)
                params = cls._params_class.build(**kwargs)
                driver = cls(params)
                driver.run(start_iteration=start_iteration)
            except GeoAppsError as error:
                logging.getLogger(__name__).warning(
                    "\n\nApplicationError: %s\n\n", error
                )
                sys.exit(1)

        return driver

    @classmethod
    def start_dask_run(cls, json_path: Path, **kwargs) -> Driver:
        """
        Sets Dask config settings.

        :param json_path: Path to input file (.ui.json) for the application.
        :param kwargs: Additional keyword arguments for the dask run.
        """
        return start_dask_run(cls, json_path, **kwargs)

    @abstractmethod
    def warm_start(self, start_iteration: int = -1):
        """
        Re-start the process where it left off
        """

    @property
    def workers(self) -> list[tuple[str]]:
        """List of workers stored as a list of tuples."""
        return self._workers


class ForwardDriver(BaseDriver):
    def __init__(
        self,
        params: BaseForwardOptions | BaseInversionOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
    ):
        super().__init__(params, client=client, workers=workers)

    def simpeg_run(self):
        """Run inversion from params"""

        predicted = self.inverse_problem.get_dpred(self.models.starting_model, None)
        self.directives.save_iteration_data_directive.write(0, predicted)

        if (
            isinstance(
                self.directives.save_iteration_data_directive,
                directives.SaveDataGeoH5,
            )
            and len(self.directives.save_iteration_data_directive.channels) > 1
        ):
            directives.SavePropertyGroup(
                self.inversion_data.entity,
                channels=self.directives.save_iteration_data_directive.channels,
                components=self.directives.save_iteration_data_directive.components,
            ).write(0)

    def start_message(self):
        if self.logger:
            self.logger.write("Running the forward simulation ...\n")

    def warm_start(self, start_iteration: int = -1):
        """
        Re-start the process where it left off
        """


class InversionDriver(BaseDriver):
    _params_class = BaseForwardOptions | BaseInversionOptions

    def __init__(
        self,
        params: BaseForwardOptions | BaseInversionOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
    ):
        super().__init__(params, client=client, workers=workers)

        self._inversion: inversion.BaseInversion | None = None
        self._optimization: optimization.ProjectedGNCG | None = None
        self._regularization: None = None

    def count_data(self):
        """
        Returns the finite (not nan) and total data counts for drivers.

        Iterates and accumulates over collection of drivers if joint inversion.
        """
        drivers = [self]
        if hasattr(self, "drivers"):
            drivers = self.drivers

        finite_data_count, total_data_count = 0, 0
        for driver in drivers:
            finite_data_count += driver.inversion_data.n_data(finite_only=True)
            total_data_count += driver.inversion_data.n_data(finite_only=False)

        return finite_data_count, total_data_count

    def get_modified_regularization(
        self,
        reg_func,
        mapping,
        is_rotated: bool,
        forward_mesh: RegularizationMesh | None,
        backward_mesh: RegularizationMesh | None,
    ):
        """
        Modify the regularization function with rotated operators.

        :param reg_func: Regularization function.
        :param mapping: Mapping.
        :param is_rotated: Whether the regularization function is rotated or not.
        :param forward_mesh: Forward mesh object.
        :param backward_mesh: Backward mesh object.
        """
        neighbors = None
        if is_rotated and not (backward_mesh or forward_mesh):
            backward_mesh = RegularizationMesh(
                self.inversion_mesh.mesh, active_cells=self.models.active_cells
            )
            neighbors = cell_neighbors(reg_func.regularization_mesh.mesh)

        # Adjustment for 2D versus 3D problems
        components = (
            "sxz"
            if (
                "2d" in self.params.inversion_type or "1d" in self.params.inversion_type
            )
            else "sxyz"
        )
        weight_names = ["alpha_s"] + [f"length_scale_{k}" for k in components[1:]]
        functions = []
        for comp, weight_name, fun in zip(components, weight_names, reg_func.objfcts):
            if getattr(self.models, weight_name) is None:
                setattr(reg_func, weight_name, 0.0)
                functions.append(fun)
                continue

            weight = mapping * getattr(self.models, weight_name)
            norm = getattr(self.models, f"{comp}_norm")
            if norm is not None:
                norm = mapping * norm

            if not isinstance(fun, SparseSmoothness):
                fun.set_weights(**{comp: weight})
                fun.norm = norm
                functions.append(fun)
                continue

            if is_rotated and not forward_mesh:
                fun = set_rotated_operators(
                    fun,
                    neighbors,
                    comp,
                    self.models.gradient_dip,
                    self.models.gradient_direction,
                )

            average_op = getattr(
                reg_func.regularization_mesh,
                f"aveCC2F{fun.orientation}",
            )
            fun.set_weights(**{comp: average_op @ weight})

            if norm is not None:
                fun.norm = np.round(average_op @ norm, decimals=3)
            functions.append(fun)

            if is_rotated:
                fun.gradient_type = "components"
                backward_fun = deepcopy(fun)
                setattr(backward_fun, "_regularization_mesh", backward_mesh)

                # Only do it once for MVI
                if not forward_mesh:
                    backward_fun = set_rotated_operators(
                        backward_fun,
                        neighbors,
                        comp,
                        self.models.gradient_dip,
                        self.models.gradient_direction,
                        forward=False,
                    )
                average_op = getattr(
                    backward_fun.regularization_mesh,
                    f"aveCC2F{fun.orientation}",
                )
                backward_fun.set_weights(**{comp: average_op @ weight})

                if norm is not None:
                    backward_fun.norm = np.round(average_op @ norm, decimals=3)
                functions.append(backward_fun)

        return functions

    def get_regularization(self):
        if self.params.forward_only:
            return BaseRegularization(mesh=self.inversion_mesh.mesh)

        reg_funcs = []
        is_rotated = self.params.models.gradient_rotation is not None
        backward_mesh = None
        forward_mesh = None
        for mapping in self.mapping:
            reg_func = Sparse(
                forward_mesh or self.inversion_mesh.mesh,
                active_cells=self.models.active_cells if forward_mesh is None else None,
                mapping=mapping,
                reference_model=self.models.reference_model,
            )

            functions = self.get_modified_regularization(
                reg_func, mapping, is_rotated, forward_mesh, backward_mesh
            )

            # Will avoid recomputing operators if the regularization mesh is the same
            forward_mesh = functions[0].regularization_mesh
            backward_mesh = functions[-1].regularization_mesh
            reg_func.objfcts = functions
            reg_func.norms = [fun.norm for fun in functions]
            reg_funcs.append(reg_func)

        return objective_function.ComboObjectiveFunction(objfcts=reg_funcs)

    @property
    def inversion(self):
        if getattr(self, "_inversion", None) is None:
            self._inversion = inversion.BaseInversion(
                self.inverse_problem, directiveList=self.directives.directive_list
            )
        return self._inversion

    @property
    def optimization(self):
        if getattr(self, "_optimization", None) is None:
            if self.params.forward_only:
                return optimization.ProjectedGNCG(cg_rtol=1.0)

            self._optimization = optimization.ProjectedGNCG(
                maxIter=self.params.optimization.max_global_iterations,
                lower=self.models.lower_bound,
                upper=self.models.upper_bound,
                maxIterLS=self.params.optimization.max_line_search_iterations,
                cg_maxiter=self.params.optimization.max_cg_iterations,
                cg_rtol=self.params.optimization.tol_cg,
                active_set_grad_scale=1e-8,
                LSshorten=0.25,
                require_decrease=False,
            )
        return self._optimization

    @property
    def regularization(self):
        if getattr(self, "_regularization", None) is None:
            with fetch_active_workspace(self.workspace, mode="r"):
                if self.logger:
                    self.logger.write("Creating the regularization functions...\n")

                self._regularization = self.get_regularization()

        return self._regularization

    @regularization.setter
    def regularization(self, regularization: objective_function.ComboObjectiveFunction):
        if not isinstance(regularization, objective_function.ComboObjectiveFunction):
            raise TypeError(
                f"Regularization must be a ComboObjectiveFunction, not {type(regularization)}."
            )
        self._regularization = regularization

    def simpeg_run(self):
        """Run inversion from params"""
        self.inversion.run(self.models.starting_model)

    def start_message(self):
        # SimPEG reports half phi_d, so we scale to match
        has_chi_start = self.params.irls.starting_chi_factor is not None
        chi_start = (
            self.params.irls.starting_chi_factor
            if has_chi_start
            else self.params.cooling_schedule.chi_factor
        )

        finite_data_count, total_data_count = self.count_data()
        rescale = finite_data_count / total_data_count
        rescaled_chi_factor = self.params.cooling_schedule.chi_factor * rescale
        rescaled_starting_chi_factor = chi_start * rescale
        self.logger.write(
            f"Target Misfit: {rescaled_chi_factor * total_data_count:.2e} ({finite_data_count} data "
            f"with chifact = {self.params.cooling_schedule.chi_factor})\n"
        )
        self.logger.write(
            f"IRLS Start Misfit: {rescaled_starting_chi_factor * total_data_count:.2e} ({finite_data_count} data "
            f"with chifact = {self.params.irls.starting_chi_factor})\n"
        )

    def warm_start(self, start_iteration: int = -1):
        """
        Re-start the process where it left off

        :param start_iteration: Iteration number to start back at.
        """
        log_file = next(
            child for child in self.out_group.children if child.name.endswith(".log")
        )
        log_file.save_file(path=self.workspace.h5file.parent, name=log_file.name)
        out_file = next(
            child for child in self.out_group.children if child.name.endswith(".out")
        )
        out_file.save_file(path=self.workspace.h5file.parent, name=out_file.name)
        out_array = read_csv(BytesIO(out_file.file_bytes), sep=" ")

        last_iter = out_array["iteration"].iloc[start_iteration]
        last_beta = out_array["beta"].iloc[start_iteration]

        if self.logger:
            self.logger.write(
                "\n\t\t###################################################\n"
                + f"\t\t\tRe-starting inversion at iteration {last_iter}\n"
                + f"\t\t\t\t{self.logger.start_date_time}\n"
                + "\t\t###################################################\n"
            )

        self._reset_on_iteration(last_iter)
        self.inverse_problem.beta = last_beta

    def _reset_on_iteration(self, start_iteration: int):
        """
        Reset the inversion parameters to a given iteration and beta value.

        Assumes that the workspace is already opened to access data.

        :param start_iteration: Iteration number to start back at.
        """

        self._reset_models(start_iteration)

        mesh = first_child_of_type(self.out_group, (DrapeModel, Octree))
        self._inversion_mesh = InversionMesh(self.workspace, self.params, entity=mesh)
        self.models.active_cells = (
            self._inversion_mesh.permutation @ mesh.get_entity("active_cells")[0].values
        ).astype(bool)

        self.optimization.iter = start_iteration
        self._reset_directives(start_iteration)

    def _reset_directives(self, iteration: int):
        """
        Reset the inversion directives based on specified iteration and model.

        :param iteration: The iteration number to reset directives for.
        """
        chi_data = [
            child
            for child in self.out_group.children
            if child.name.endswith(".chi") and isinstance(child, FilenameData)
        ]

        if chi_data:
            chi_array = np.loadtxt(BytesIO(chi_data[0].file_bytes), skiprows=1)

            if self.directives.scale_misfits is not None:
                self.directives.scale_misfits.scalings = chi_array[iteration, 1:]
                self.directives.scale_misfits.multipliers = np.asarray(
                    self.data_misfit.multipliers
                )
                self.data_misfit.multipliers *= self.directives.scale_misfits.scalings

        # Hard-wire beta and remove estimator directive
        directive = self.directives.beta_estimate_by_eigenvalues_directive
        if directive is not None and directive in self.directives.directive_list:
            self.directives.directive_list.remove(
                self.directives.beta_estimate_by_eigenvalues_directive
            )

    def _reset_models(self, iteration: int):
        """
        Reset the inversion models based on specified iteration and mesh.

        :param iteration: The iteration number to reset the models for.
        """
        mesh = first_child_of_type(self.out_group, (DrapeModel, Octree))
        flag = f"Iteration_{iteration}_"
        for child in mesh.children:
            if flag in child.name:
                self.params.models.starting_model = child
                return

        raise GeoAppsError(
            f"Could not reset the inversion at iteration {iteration}, no model found."
        )


def first_child_of_type(entity, child_type: type | tuple):
    """
    Get the first child of a given type from an entity.

    :param entity: The parent entity to search for children.
    :param child_type: The type of child to find.
    :return: The first child of the specified type.
    """
    for child in entity.children:
        if isinstance(child, child_type):
            return child
    raise GeoAppsError(f"No child of type {child_type} found in {entity.name}.")


class InversionLogger:
    """
    Logger for the inversion process.

    Writes messages to both the terminal and a log file in the same directory as the workspace.

    :param driver: The inversion driver to log for.
    """

    def __init__(self, driver):
        self.driver = driver
        self.terminal = sys.stdout

        self.initial_time = time()
        self.start_date_time = datetime.now().strftime("%Y/%m/%d %Hh:%Mm:%Ss")
        self.logfile = (
            Path(self.driver.workspace.h5file).parent
            / f"{self.driver.workspace.h5file.stem}.log"
        )

    def start(self):
        self.write(
            f"Running simpeg-drivers {__version__}\n"
            f"Started {self.start_date_time}\n"
            f"{self.driver.params.title}\n"
        )

    def end(self):
        elapsed_time = timedelta(seconds=int(time() - self.initial_time))
        self.write(f"Total runtime: {elapsed_time}\n")

    def write(self, message):
        self.terminal.write(message)
        with open(self.logfile, "a", encoding="utf8") as logfile:
            logfile.write(message)
            logfile.flush()

    def close(self):
        self.terminal.close()

    def flush(self):
        pass


def validate_client(client: Client | bool | None) -> Client | bool:
    """
    Validate or create a Dask client.
    """
    if client is None:
        try:
            client = get_client()
        except ValueError:
            client = False
    return client


def validate_workers(client, workers: list[tuple[str]] | None) -> list[tuple[str]]:
    """
    Validate the list of workers.
    """
    if client:
        available_workers = [(worker,) for worker in client.nthreads()]
    else:
        return []

    if workers is None:
        return available_workers

    if not isinstance(workers, list) or not all(isinstance(w, tuple) for w in workers):
        raise TypeError("Workers must be a list of tuple[str].")

    invalid_workers = [w for w in workers if w not in available_workers]
    if invalid_workers:
        raise ValueError(
            f"The following workers are not available: {invalid_workers}. "
            f"Available workers are: {available_workers}."
        )

    return workers


if __name__ == "__main__":
    file, args = argument_parser()

    input_file = UIJson.read(file).flatten()
    driver_class = driver_class_from_dict(input_file)

    driver_class.start_dask_run(file, **args)
