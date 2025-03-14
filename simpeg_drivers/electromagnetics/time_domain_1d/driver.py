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
from geoh5py.objects import DrapeModel
from geoh5py.ui_json.ui_json import fetch_active_workspace

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
            with fetch_active_workspace(self.workspace, mode="r+"):
                paddings = [
                    self.params.drape_model.horizontal_padding,
                    self.params.drape_model.horizontal_padding,
                    self.params.drape_model.vertical_padding,
                    1,
                ]

                entity = get_drape_model(
                    self.workspace,
                    "Models",
                    self.params.data_object.vertices,
                    [
                        self.params.drape_model.u_cell_size,
                        self.params.drape_model.v_cell_size,
                    ],
                    self.params.drape_model.depth_core,
                    paddings,
                    self.params.drape_model.expansion_factor,
                )[0]

            self._inversion_mesh = InversionMesh(
                self.workspace, self.params, entity=entity
            )

        return self._inversion_mesh


class TDEM1DForwardDriver(Base1DDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = TDEM1DForwardOptions
    _validations = None


class TDEM1DInversionDriver(Base1DDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEM1DInversionOptions
    _validations = None
