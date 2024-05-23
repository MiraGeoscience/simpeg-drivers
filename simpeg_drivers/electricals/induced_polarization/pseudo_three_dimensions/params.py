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

from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.constants import (
    default_ui_json,
    forward_defaults,
    inversion_defaults,
    validations,
)
from simpeg_drivers.electricals.params import BasePseudo3DParams


class InducedPolarizationPseudo3DParams(BasePseudo3DParams):
    """
    Parameter class for electrical->chargeability inversion.
    """

    _physical_property = "chargeability"
    _inversion_type = "induced polarization pseudo 3d"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._validations = validations
        self._conductivity_model: float | None = 1e-3
        self._chargeability_channel_bool: bool = True
        self._chargeability_channel = None
        self._chargeability_uncertainty = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def conductivity_model(self):
        return self._conductivity_model

    @conductivity_model.setter
    def conductivity_model(self, value):
        self.setter_validator("conductivity_model", value)

    @property
    def chargeability_channel_bool(self):
        return self._chargeability_channel_bool

    @chargeability_channel_bool.setter
    def chargeability_channel_bool(self, value):
        self.setter_validator("chargeability_channel_bool", value)

    @property
    def chargeability_channel(self):
        return self._chargeability_channel

    @chargeability_channel.setter
    def chargeability_channel(self, value):
        self.setter_validator("chargeability_channel", value)

    @property
    def chargeability_uncertainty(self):
        return self._chargeability_uncertainty

    @chargeability_uncertainty.setter
    def chargeability_uncertainty(self, value):
        self.setter_validator("chargeability_uncertainty", value)
