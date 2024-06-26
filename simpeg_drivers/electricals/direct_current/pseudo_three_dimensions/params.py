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

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.constants import (
    default_ui_json,
    forward_defaults,
    inversion_defaults,
    validations,
)
from simpeg_drivers.electricals.params import BasePseudo3DParams


class DirectCurrentPseudo3DParams(BasePseudo3DParams):
    """
    Parameter class for electrical->conductivity inversion.
    """

    _physical_property = "conductivity"
    _inversion_type = "direct current 3d"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._validations = validations
        self._potential_channel_bool = None
        self._potential_channel = None
        self._potential_uncertainty = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def potential_channel_bool(self):
        return self._potential_channel_bool

    @potential_channel_bool.setter
    def potential_channel_bool(self, val):
        self.setter_validator("potential_channel_bool", val)

    @property
    def potential_channel(self):
        return self._potential_channel

    @potential_channel.setter
    def potential_channel(self, val):
        self.setter_validator("potential_channel", val, fun=self._uuid_promoter)

    @property
    def potential_uncertainty(self):
        return self._potential_uncertainty

    @potential_uncertainty.setter
    def potential_uncertainty(self, val):
        self.setter_validator("potential_uncertainty", val, fun=self._uuid_promoter)
