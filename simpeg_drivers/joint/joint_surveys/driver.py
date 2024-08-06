# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import numpy as np
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import maps

from simpeg_drivers.components.factories import DirectivesFactory
from simpeg_drivers.joint.driver import BaseJointDriver

from .constants import validations
from .params import JointSurveysParams


class JointSurveyDriver(BaseJointDriver):
    _params_class = JointSurveysParams
    _validations = validations

    def __init__(self, params: JointSurveysParams):
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

                if self.drivers[0].models.is_sigma:
                    model = np.exp(model)

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
                    driver_directives = DirectivesFactory(driver)

                    save_model = driver_directives.save_iteration_model_directive
                    save_model.transforms = [
                        driver.data_misfit.model_map,
                        *save_model.transforms,
                    ]
                    directives_list.append(save_model)

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

                self._directives = DirectivesFactory(self)
                global_model_save = self._directives.save_iteration_model_directive
                if self.models.is_sigma:
                    global_model_save.transforms += [
                        maps.ExpMap(self.inversion_mesh.mesh)
                    ]

                self._directives.directive_list = [
                    *self._directives.inversion_directives,
                    global_model_save,
                    *directives_list,
                ]
        return self._directives
