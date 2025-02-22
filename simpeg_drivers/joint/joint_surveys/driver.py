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

from logging import getLogger

import numpy as np
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import maps

from simpeg_drivers.components.factories import DirectivesFactory, SaveModelGeoh5Factory
from simpeg_drivers.joint.driver import BaseJointDriver

from .params import JointSurveysOptions


logger = getLogger(__name__)


class JointSurveyDriver(BaseJointDriver):
    """Joint surveys inversion driver"""

    _params_class = JointSurveysOptions
    _validations = None

    def __init__(self, params: JointSurveysOptions):
        super().__init__(params)

        with fetch_active_workspace(self.workspace, mode="r+"):
            self.initialize()

    def validate_create_models(self):
        """Check if all models were provided, otherwise use the first driver models."""
        for model_type in self.models.model_types:
            model_class = getattr(self.models, model_type)
            if (
                model_class is None
                and getattr(self.drivers[0].models, model_type) is not None
            ):
                model_local_values = getattr(self.drivers[0].models, model_type)
                projection = (
                    self.drivers[0]
                    .data_misfit.model_map.deriv(np.ones(self.models.n_active))
                    .T
                )
                norm = np.array(np.sum(projection, axis=1)).flatten()
                model = (projection * model_local_values) / (norm + 1e-8)

                if self.drivers[0].models.is_sigma and model_type in [
                    "starting",
                    "reference",
                    "lower_bound",
                    "upper_bound",
                    "conductivity",
                ]:
                    model = np.exp(model)
                    if (
                        getattr(self.params, "model_type", None)
                        == "Resistivity (Ohm-m)"
                    ):
                        logger.info(
                            "Converting input %s model to %s",
                            model_type,
                            getattr(self.params, "model_type", None),
                        )
                        model = 1.0 / model

                getattr(self.models, f"_{model_type}").model = model

    @property
    def wires(self):
        """Model projections"""
        if self._wires is None:
            wires = [maps.IdentityMap(nP=self.models.n_active) for _ in self.drivers]
            self._wires = wires

        return self._wires

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None and not self.params.forward_only:
            with fetch_active_workspace(self.workspace, mode="r+"):
                directives_list = []
                count = 0
                for driver in self.drivers:
                    if getattr(driver.params, "model_type", None) is not None:
                        driver.params.model_type = self.params.model_type

                    driver_directives = DirectivesFactory(driver)

                    save_model = driver_directives.save_iteration_model_directive
                    save_model.transforms = [
                        driver.data_misfit.model_map,
                        *save_model.transforms,
                    ]

                    directives_list.append(save_model)

                    if driver_directives.save_property_group is not None:
                        directives_list.append(driver_directives.save_property_group)

                    n_tiles = len(driver.data_misfit.objfcts)
                    for name in [
                        "save_iteration_data_directive",
                        "save_iteration_residual_directive",
                        "save_iteration_apparent_resistivity_directive",
                        "vector_inversion_directive",
                    ]:
                        directive = getattr(driver_directives, name)
                        if directive is not None:
                            directive.joint_index = [
                                count + ii for ii in range(n_tiles)
                            ]
                            directives_list.append(directive)

                    count += n_tiles

                model_factory = SaveModelGeoh5Factory(self.params)
                model_factory.factory_type = self.drivers[0].params.inversion_type
                global_model_save = model_factory.build(
                    inversion_object=self.inversion_mesh,
                    active_cells=self.models.active_cells,
                    name="Model",
                )

                self._directives = DirectivesFactory(self)
                if self._directives.save_property_group is not None:
                    directives_list.append(self._directives.save_property_group)

                directives_list.append(self._directives.save_iteration_log_files)

                self._directives.directive_list = [
                    *self._directives.inversion_directives,
                    global_model_save,
                    *directives_list,
                ]
        return self._directives
