# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=unexpected-keyword-arg, no-value-for-parameter

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

from geoh5py.shared.utils import fetch_active_workspace
from simpeg import directives, maps
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import CrossGradient

from simpeg_drivers.joint.driver import BaseJointDriver
from simpeg_drivers.joint.joint_cross_gradient.options import JointCrossGradientOptions


class JointCrossGradientDriver(BaseJointDriver):
    _params_class = JointCrossGradientOptions

    def __init__(self, params: JointCrossGradientOptions):
        self._wires = None
        self._directives = None

        super().__init__(params)

    def get_regularization(self):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """
        # Trick the drivers by swapping the inversion_mesh and models
        # such that the regularization uses the global mesh
        multipliers, reg_list = [], []
        for driver in self.drivers:
            # Pre-store the saving directives before the swap
            _ = driver.directives.save_directives

            driver._models = self.models  # pylint: disable=protected-access
            driver._inversion_mesh = self.inversion_mesh  # pylint: disable=protected-access
            driver._n_values = self.models.n_active  # pylint: disable=protected-access
            driver.mapping = [
                self._mapping[driver, mapping] for mapping in driver.mapping
            ]

            # Swap in stored map
            for mapping in driver.mapping:
                self._mapping[driver, mapping] = mapping

            for multiplier, objfct in driver.regularization:
                multipliers.append(multiplier)
                reg_list.append(objfct)

        for label, driver_pairs in zip(
            ["a_b", "c_a", "c_b"], combinations(self.drivers, 2), strict=False
        ):
            # Deal with MVI components
            for count_a, mapping_a in enumerate(driver_pairs[0].mapping):
                for count_b, mapping_b in enumerate(driver_pairs[1].mapping):
                    wires = maps.Wires(
                        ("a", self._mapping[driver_pairs[0], mapping_a]),
                        ("b", self._mapping[driver_pairs[1], mapping_b]),
                    )
                    reg_list.append(
                        CrossGradient(
                            self.inversion_mesh.mesh,
                            wires,
                            active_cells=self.models.active_cells,
                            units=[
                                "metric" if not count_a else "component",
                                "metric" if not count_b else "component",
                            ],
                        )
                    )
                    multiplier = getattr(self.params, f"cross_gradient_weight_{label}")

                    # Fixed dimensional scaling if not iterative
                    if not self.params.iterative_rescaling:
                        multiplier *= (
                            reg_list[-1].regularization_mesh.base_length ** 4.0
                        )

                    multipliers.append(multiplier)

        return ComboObjectiveFunction(objfcts=reg_list, multipliers=multipliers)

    def _get_joint_directives(self) -> list[directives.Directive]:
        """
        Create a list of directives for the joint inversion.
        """
        regularization = self.regularization  # Pre-compute the regularization
        directives_list = super()._get_joint_directives()

        if self.params.iterative_rescaling:
            for reg in regularization.objfcts:
                if isinstance(reg, CrossGradient):
                    directives_list.append(
                        directives.ScaleMaximumDerivatives(reg)
                    )  # Update preconditioner after each iteration to account for cross-gradient regularization

        return directives_list

    def _reset_directives(self, iteration):
        """
        Reset the inversion parameters to a given iteration and beta value.

        Assumes that the workspace is already opened to access data.
        """
        super()._reset_directives(iteration)

        for directive in self.directives.directive_list:
            if isinstance(directive, directives.ScaleMaximumDerivatives):
                directive.scale_on_current_model(self.models.starting_model)


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    JointCrossGradientDriver.start_dask_run(file)
