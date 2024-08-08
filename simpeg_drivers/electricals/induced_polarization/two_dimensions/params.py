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

from simpeg_drivers.electricals.params import Base2DParams

from .constants import (
    default_ui_json,
    forward_defaults,
    inversion_defaults,
    validations,
)


class InducedPolarization2DParams(Base2DParams):
    """
    Parameter class for electrical->induced polarization (IP) inversion.
    """

    _physical_property = "chargeability"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._inversion_type = "induced polarization 2d"
        self._validations = validations
        self._chargeability_channel_bool = None
        self._chargeability_channel = None
        self._chargeability_uncertainty = None
        self._line_object = None
        self._line_id = None
        self._conductivity_model_object = None
        self._conductivity_model = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def chargeability_channel_bool(self):
        return self._chargeability_channel_bool

    @chargeability_channel_bool.setter
    def chargeability_channel_bool(self, val):
        self.setter_validator("chargeability_channel_bool", val)

    @property
    def chargeability_channel(self):
        return self._chargeability_channel

    @chargeability_channel.setter
    def chargeability_channel(self, val):
        self.setter_validator("chargeability_channel", val, fun=self._uuid_promoter)

    @property
    def chargeability_uncertainty(self):
        return self._chargeability_uncertainty

    @chargeability_uncertainty.setter
    def chargeability_uncertainty(self, val):
        self.setter_validator("chargeability_uncertainty", val, fun=self._uuid_promoter)

    @property
    def conductivity_model_object(self):
        return self._conductivity_model_object

    @conductivity_model_object.setter
    def conductivity_model_object(self, val):
        self.setter_validator("conductivity_model_object", val, fun=self._uuid_promoter)

    @property
    def conductivity_model(self):
        return self._conductivity_model

    @conductivity_model.setter
    def conductivity_model(self, val):
        self.setter_validator("conductivity_model", val, fun=self._uuid_promoter)
