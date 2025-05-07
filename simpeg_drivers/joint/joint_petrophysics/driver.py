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

from itertools import combinations

import numpy as np
from geoh5py.groups.property_group_type import GroupTypeEnum
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import directives, maps
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import PGI

from simpeg_drivers.components.factories import (
    DirectivesFactory,
    SaveModelGeoh5Factory,
)
from simpeg_drivers.joint.driver import BaseJointDriver

from .options import JointPetrophysicsOptions


class JointPetrophysicsDriver(BaseJointDriver):
    _options_class = JointPetrophysicsOptions
    _validations = None

    def __init__(self, params: JointPetrophysicsOptions):
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

        return ComboObjectiveFunction(objfcts=reg_list, multipliers=multipliers)
