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

import numpy as np
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import maps

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.joint.driver import BaseJointDriver
from simpeg_drivers.options import ModelTypeEnum

from .options import JointSurveysOptions


logger = getLogger(__name__)


class JointSurveyDriver(BaseJointDriver):
    """Joint surveys inversion driver"""

    _params_class = JointSurveysOptions

    def __init__(self, params: JointSurveysOptions):
        super().__init__(params)

        with fetch_active_workspace(self.workspace, mode="r+"):
            self.initialize()

    def validate_create_models(self):
        """Check if all models were provided, otherwise use the first driver models."""
        # Create projection for first driver to global mesh
        mapping = maps.TileMap(
            self.inversion_mesh.mesh,
            self.models.active_cells,
            self.drivers[0].inversion_mesh.mesh,
            enforce_active=False,
        )
        projection = mapping.deriv(np.ones(self.models.n_active)).T
        norm = np.array(np.sum(projection, axis=1)).flatten()

        for model_type in self.models.model_types:
            model = getattr(self.models, model_type)
            if model is not None or getattr(self.drivers[0].models, model_type) is None:
                continue

            model_local_values = getattr(self.drivers[0].models, model_type)
            model = (
                projection * model_local_values[: self.drivers[0].models.n_active]
            ) / (norm + 1e-8)

            if self.drivers[0].models.is_sigma and model_type in [
                "starting_model",
                "reference_model",
                "lower_bound",
                "upper_bound",
                "conductivity_model",
            ]:
                model = np.exp(model)
                if (
                    getattr(self.params.models, "model_type", None)
                    == ModelTypeEnum.resistivity
                ):
                    model = 1.0 / model

            getattr(self.models, f"_{model_type}").model = model

        # For MVI, set is_vector from first driver
        self.models.is_vector = self.drivers[0].models.is_vector

    @property
    def wires(self):
        """Model projections"""
        if self._wires is None:
            wires = [
                maps.IdentityMap(nP=self.models.n_active * driver.n_blocks)
                for driver in self.drivers
            ]
            self._wires = wires

        return self._wires

    def _get_global_model_save_directives(self):
        """
        Create a list of directives for regularization models.
        """
        directives_list = self._get_local_model_save_directives(
            self.drivers[0], self.wires[0]
        )

        return directives_list


JointSurveyDriver.n_values = InversionDriver.n_values
JointSurveyDriver.mapping = InversionDriver.mapping
