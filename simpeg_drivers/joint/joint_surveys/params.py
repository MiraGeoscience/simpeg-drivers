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


class JointSurveysParams(BaseJointParams):
    """
    Parameter class for gravity->density inversion.
    """

    _physical_property = ""

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._inversion_type = "joint surveys"
        self._validations = validations
        self._model_type = "Conductivity (S/m)"

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def model_type(self):
        """Model units."""
        return self._model_type

    @model_type.setter
    def model_type(self, val):
        self.setter_validator("model_type", val)

    @property
    def physical_property(self):
        """Physical property to invert."""
        return self._physical_property

    @physical_property.setter
    def physical_property(self, val: list[str]):
        unique_properties = list(set(val))
        if len(unique_properties) > 1:
            raise ValueError(
                "All physical properties must be the same. "
                f"Provided SimPEG groups for {unique_properties}."
            )
        self._physical_property = unique_properties[0]
