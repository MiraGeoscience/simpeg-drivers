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

from copy import deepcopy

from simpeg_drivers.joint.params import BaseJointParams

from .constants import default_ui_json, inversion_defaults, validations


class JointCrossGradientParams(BaseJointParams):
    """
    Parameter class for joint cross-gradient inversion.
    """

    _physical_property = [""]

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._inversion_type = "joint cross gradient"
        self._validations = validations
        self._cross_gradient_weight_a_b = 1.0
        self._cross_gradient_weight_c_a = 1.0
        self._cross_gradient_weight_c_b = 1.0

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def cross_gradient_weight_a_b(self):
        return self._cross_gradient_weight_a_b

    @cross_gradient_weight_a_b.setter
    def cross_gradient_weight_a_b(self, val):
        self.setter_validator("cross_gradient_weight_a_b", val)

    @property
    def cross_gradient_weight_c_a(self):
        return self._cross_gradient_weight_c_a

    @cross_gradient_weight_c_a.setter
    def cross_gradient_weight_c_a(self, val):
        self.setter_validator("cross_gradient_weight_c_a", val)

    @property
    def cross_gradient_weight_c_b(self):
        return self._cross_gradient_weight_c_b

    @cross_gradient_weight_c_b.setter
    def cross_gradient_weight_c_b(self, val):
        self.setter_validator("cross_gradient_weight_c_b", val)

    @property
    def physical_property(self):
        """Physical property to invert."""
        return self._physical_property

    @physical_property.setter
    def physical_property(self, val: list[str]):
        self._physical_property = val
