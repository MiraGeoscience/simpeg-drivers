# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Any

import numpy as np
from discretize import TensorMesh
from discretize.utils import mesh_utils
from geoapps_utils.utils.locations import topo_drape_elevation
from geoh5py import Workspace
from geoh5py.objects import Surface
from geoh5py.shared.merging.drape_model import DrapeModelMerger
from geoh5py.ui_json.ui_json import fetch_active_workspace
from numpy import ndarray

from simpeg_drivers.components.factories import SimulationFactory
from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.utils.utils import (
    get_default_parallelization_params,
    xyz_2_drape_model,
)


logger = getLogger(__name__)


class Base1DDriver(BaseDriver):
    """Base 1D driver for electromagnetic simulations."""

    _params_class = None

    def __init__(self, workspace: Workspace, **kwargs):
        super().__init__(workspace, **kwargs)

        self.layers_mesh: TensorMesh = self.get_1d_mesh()
        self.topo_z_drape = topo_drape_elevation(
            self.params.data_object.vertices,
            self.inversion_topography.locations,
            triangulation=self.params.active_cells.topography_object.cells
            if isinstance(self.params.active_cells.topography_object, Surface)
            else None,
        )

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                drape_models = []
                temp_work = Workspace()
                for part in self.params.data_object.unique_parts:
                    indices = self.params.data_object.parts == part
                    drape_models.append(
                        xyz_2_drape_model(
                            temp_work,
                            self.topo_z_drape[indices],
                            self.layers_mesh.h[0][::-1],
                        )
                    )

                entity = DrapeModelMerger.create_object(
                    self.workspace, drape_models, parent=self.out_group
                )

            self._inversion_mesh = InversionMesh(
                self.workspace, self.params, entity=entity
            )

        return self._inversion_mesh

    def get_1d_mesh(self) -> TensorMesh:
        layers_mesh = mesh_utils.mesh_builder_xyz(
            np.c_[0],
            np.r_[self.params.drape_model.v_cell_size],
            padding_distance=[
                [self.params.drape_model.vertical_padding, 0],
            ],
            depth_core=self.params.drape_model.depth_core,
            expansion_factor=self.params.drape_model.expansion_factor,
            mesh_type="tensor",
        )
        return layers_mesh

    def get_tiles(self) -> dict[None, list[list[ndarray[tuple[Any, ...]]]]]:
        n_data = self.inversion_data.mask.sum()
        indices = np.arange(n_data)

        # Heuristic to avoid too many chunks
        n_chunks = n_data // self.params.compute.max_chunk_size

        if self.workers:
            n_chunks /= len(self.workers)
            n_chunks = int(n_chunks) * len(self.workers)

        n_chunks = np.max([n_chunks, 1, len(self.workers)])
        return {None: [[tile] for tile in np.array_split(indices, n_chunks)]}

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
                topo=[0, 0, -np.inf],  # Bypass check for global simulation
            )

            self._simulation.mesh = self.inversion_mesh.mesh
            self._simulation.layers_mesh = self.layers_mesh
            self._simulation.active_cells = self.topo_z_drape

            # Remove cached filters for pickling
            if hasattr(self._simulation, "_fhtfilt"):
                self._simulation._fhtfilt = None  # pylint: disable=protected-access

            if hasattr(self._simulation, "_fftfilt"):
                self._simulation._fftfilt = None  # pylint: disable=protected-access

        return self._simulation

    @classmethod
    def start_dask_run(
        cls, json_path: Path, n_workers: int | None = None, n_threads: int | None = None
    ):
        """Overload configurations of BaseDriver Dask config settings."""
        n_workers, n_threads = get_default_parallelization_params(json_path)

        super().start_dask_run(json_path, n_workers=n_workers, n_threads=n_threads)
