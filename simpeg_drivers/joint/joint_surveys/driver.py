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
from geoh5py.objects import DrapeModel, Octree
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import directives, maps

from simpeg_drivers.driver import InversionDriver, first_child_of_type
from simpeg_drivers.joint.driver import BaseJointDriver
from simpeg_drivers.joint.joint_surveys.options import JointSurveysOptions
from simpeg_drivers.options import ModelTypeEnum
from simpeg_drivers.utils.utils import argument_parser


logger = getLogger(__name__)


class JointSurveysDriver(BaseJointDriver):
    """Joint surveys inversion driver"""

    _params_class = JointSurveysOptions

    def get_regularization(self):
        """
        Overload the regularization using the method of the first driver.
        """
        driver = self.drivers[0]
        # Pre-store the saving directives before the swap
        _ = driver.directives.save_directives

        driver._models = self.models  # pylint: disable=protected-access
        driver._inversion_mesh = self.inversion_mesh  # pylint: disable=protected-access
        driver._n_values = self.models.n_active  # pylint: disable=protected-access
        driver.mapping = self.mapping
        return driver.get_regularization()

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

            # All get augmented to 3N for vector models
            if self.drivers[0].models.is_vector and "clination" not in model_type:
                model_local_values = getattr(
                    self.drivers[0].models, f"_{model_type}"
                ).model

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

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None and not self.params.forward_only:
            with fetch_active_workspace(self.workspace, mode="r+"):
                directives_list = self._get_joint_directives()

                if self.models.is_vector:
                    for directive in directives_list:
                        if isinstance(directive, directives.VectorInversion):
                            directives_list.remove(directive)

                    reference_angles = (
                        getattr(self.params.models, "reference_model", None)
                        is not None,
                        getattr(self.params.models, "reference_inclination", None)
                        is not None,
                        getattr(self.params.models, "reference_declination", None)
                        is not None,
                    )

                    vector_directive = directives.VectorInversion(
                        self.data_misfit.objfcts,
                        self.regularization,
                        chifact_target=self.params.cooling_schedule.chi_factor * 2,
                        reference_angles=reference_angles,
                    )

                    directives_list = [vector_directive] + directives_list

                self._directives.directive_list = directives_list

        return self._directives

    def _reset_models(self, iteration):
        """
        Reset the inversion models based on specified iteration.

        :param iteration: The iteration number to reset the models for.
        """
        mesh = first_child_of_type(self.out_group, (DrapeModel, Octree))
        flag = f"Iteration_{iteration}_"
        for child in mesh.children:
            if flag in child.name:
                self.params.models.starting_model = child
                break

        super()._reset_models(iteration)


JointSurveysDriver.n_values = InversionDriver.n_values
JointSurveysDriver.mapping = InversionDriver.mapping

if __name__ == "__main__":
    file, args = argument_parser()
    JointSurveysDriver.start_dask_run(file, **args)
