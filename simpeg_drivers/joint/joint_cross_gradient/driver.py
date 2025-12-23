# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=unexpected-keyword-arg, no-value-for-parameter

from __future__ import annotations

from itertools import combinations

import numpy as np
from geoh5py.groups.property_group_type import GroupTypeEnum
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import directives, maps
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import CrossGradient

from simpeg_drivers.components.factories import (
    DirectivesFactory,
    SaveModelGeoh5Factory,
)
from simpeg_drivers.joint.driver import BaseJointDriver

from .options import JointCrossGradientOptions


class JointCrossGradientDriver(BaseJointDriver):
    _params_class = JointCrossGradientOptions

    def __init__(self, params: JointCrossGradientOptions):
        self._wires = None
        self._directives = None

        super().__init__(params)

        with fetch_active_workspace(self.workspace, mode="r+"):
            self.initialize()

    def get_regularization(self):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """
        regularizations = super().get_regularization()
        reg_list, multipliers = self._overload_regularization(regularizations)

        for label, driver_pairs in zip(
            ["a_b", "c_a", "c_b"], combinations(self.drivers, 2), strict=False
        ):
            # Deal with MVI components
            for mapping_a in driver_pairs[0].mapping:
                for mapping_b in driver_pairs[1].mapping:
                    wires = maps.Wires(
                        ("a", self._mapping[driver_pairs[0], mapping_a]),
                        ("b", self._mapping[driver_pairs[1], mapping_b]),
                    )
                    reg_list.append(
                        CrossGradient(
                            self.inversion_mesh.mesh,
                            wires,
                            active_cells=self.models.active_cells,
                        )
                    )
                    base_multipier = (
                        reg_list[-1].regularization_mesh.base_length ** 4.0
                    )  # Account for cross of length scale square
                    multipliers.append(
                        getattr(self.params, f"cross_gradient_weight_{label}")
                        * base_multipier
                    )

        return ComboObjectiveFunction(objfcts=reg_list, multipliers=multipliers)
