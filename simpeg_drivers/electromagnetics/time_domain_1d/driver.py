# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import numpy as np
from geoh5py import Workspace
from geoh5py.shared.merging.drape_model import DrapeModelMerger
from geoh5py.ui_json.ui_json import fetch_active_workspace

from simpeg_drivers.components.factories import MisfitFactory
from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.utils import get_drape_model

from .params import (
    TDEM1DForwardOptions,
    TDEM1DInversionOptions,
)


class Base1DDriver(InversionDriver):
    """Base 1D driver for electromagnetic simulations."""

    _params_class = None
    _validations = None

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            temp_workspace = Workspace()
            with fetch_active_workspace(self.workspace, mode="r+"):
                paddings = [
                    self.params.drape_model.horizontal_padding,
                    self.params.drape_model.horizontal_padding,
                    self.params.drape_model.vertical_padding,
                    1,
                ]
                drape_models = []
                for part in self.params.data_object.unique_parts:
                    indices = self.params.data_object.parts == part

                    drape_models.append(
                        get_drape_model(
                            temp_workspace,
                            "Models",
                            self.params.data_object.vertices[
                                indices, :
                            ],  # Drape on topography
                            [
                                self.params.drape_model.u_cell_size,
                                self.params.drape_model.v_cell_size,
                            ],
                            self.params.drape_model.depth_core,
                            paddings,
                            self.params.drape_model.expansion_factor,
                            draped_layers=True,
                        )[0]
                    )

                entity = DrapeModelMerger.create_object(self.workspace, drape_models)

            self._inversion_mesh = InversionMesh(
                self.workspace, self.params, entity=entity
            )

        return self._inversion_mesh

    @property
    def data_misfit(self):
        """The Simpeg.data_misfit class"""
        if getattr(self, "_data_misfit", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                # Tile locations
                tiles = self.get_tiles()

                print(f"Setting up {len(tiles)} tile(s) . . .")
                # Build tiled misfits and combine to form global misfit
                self._data_misfit, self._sorting, self._ordering = MisfitFactory(
                    self.params, models=self.models
                ).build(
                    tiles,
                    self.inversion_data,
                    self.inversion_mesh.mesh,
                    self.inversion_mesh.entity.prisms[:, :3],
                )
                print("Done.")

                self.inversion_data.save_data()
                self._data_misfit.multipliers = np.asarray(
                    self._data_misfit.multipliers, dtype=float
                )

            if self.client:
                self.distributed_misfits()

        return self._data_misfit


class TDEM1DForwardDriver(Base1DDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = TDEM1DForwardOptions
    _validations = None


class TDEM1DInversionDriver(Base1DDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEM1DInversionOptions
    _validations = None
