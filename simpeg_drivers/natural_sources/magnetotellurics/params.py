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
from uuid import UUID

from simpeg_drivers import InversionBaseParams

from .constants import (
    default_ui_json,
    forward_defaults,
    inversion_defaults,
    validations,
)


class MagnetotelluricsParams(InversionBaseParams):
    """
    Parameter class for magnetotelluric->conductivity inversion.
    """

    _physical_property = "conductivity"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._inversion_type = "magnetotellurics"
        self._validations = validations
        self._zxx_real_channel_bool = None
        self._zxx_real_channel = None
        self._zxx_real_uncertainty = None
        self._zxx_imag_channel_bool = None
        self._zxx_imag_channel = None
        self._zxx_imag_uncertainty = None
        self._zxy_real_channel_bool = None
        self._zxy_real_channel = None
        self._zxy_real_uncertainty = None
        self._zxy_imag_channel_bool = None
        self._zxy_imag_channel = None
        self._zxy_imag_uncertainty = None
        self._zyx_real_channel_bool = None
        self._zyx_real_channel = None
        self._zyx_real_uncertainty = None
        self._zyx_imag_channel_bool = None
        self._zyx_imag_channel = None
        self._zyx_imag_uncertainty = None
        self._zyy_real_channel_bool = None
        self._zyy_real_channel = None
        self._zyy_real_uncertainty = None
        self._zyy_imag_channel_bool = None
        self._zyy_imag_channel = None
        self._zyy_imag_uncertainty = None
        self._background_conductivity = None
        self._model_type = "Conductivity (S/m)"

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    def data_channel(self, component: str):
        """Return uuid of data channel."""
        return getattr(self, "_".join([component, "channel"]), None)

    def uncertainty_channel(self, component: str):
        """Return uuid of uncertainty channel."""
        return getattr(self, "_".join([component, "uncertainty"]), None)

    def property_group_data(self, property_group: UUID):
        data = {}
        frequencies = self.data_object.channels
        if self.forward_only:
            return {k: None for k in frequencies}
        else:
            group = next(
                k
                for k in self.data_object.property_groups
                if k.uid == property_group.uid
            )
            property_names = [
                self.geoh5.get_entity(p)[0].name for p in group.properties
            ]
            properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
            for i, f in enumerate(frequencies):
                try:
                    f_ind = property_names.index(
                        next(k for k in property_names if f"{f:.2e}" in k)
                    )  # Safer if data was saved with geoapps naming convention
                    data[f] = properties[f_ind]
                except StopIteration:
                    data[f] = properties[i]  # in case of other naming conventions

            return data

    def data(self, component: str):
        """Returns array of data for chosen data component."""
        property_group = self.data_channel(component)
        return self.property_group_data(property_group)

    def uncertainty(self, component: str) -> float:
        """Returns uncertainty for chosen data component."""
        uid = self.uncertainty_channel(component)
        return self.property_group_data(uid)

    @property
    def model_type(self):
        """Model units."""
        return self._model_type

    @model_type.setter
    def model_type(self, val):
        self.setter_validator("model_type", val)

    @property
    def zxx_real_channel_bool(self):
        return self._zxx_real_channel_bool

    @zxx_real_channel_bool.setter
    def zxx_real_channel_bool(self, val):
        self.setter_validator("zxx_real_channel_bool", val)

    @property
    def zxx_real_channel(self):
        return self._zxx_real_channel

    @zxx_real_channel.setter
    def zxx_real_channel(self, val):
        self.setter_validator("zxx_real_channel", val, fun=self._uuid_promoter)

    @property
    def zxx_real_uncertainty(self):
        return self._zxx_real_uncertainty

    @zxx_real_uncertainty.setter
    def zxx_real_uncertainty(self, val):
        self.setter_validator("zxx_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zxx_imag_channel_bool(self):
        return self._zxx_imag_channel_bool

    @zxx_imag_channel_bool.setter
    def zxx_imag_channel_bool(self, val):
        self.setter_validator("zxx_imag_channel_bool", val)

    @property
    def zxx_imag_channel(self):
        return self._zxx_imag_channel

    @zxx_imag_channel.setter
    def zxx_imag_channel(self, val):
        self.setter_validator("zxx_imag_channel", val, fun=self._uuid_promoter)

    @property
    def zxx_imag_uncertainty(self):
        return self._zxx_imag_uncertainty

    @zxx_imag_uncertainty.setter
    def zxx_imag_uncertainty(self, val):
        self.setter_validator("zxx_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zxy_real_channel_bool(self):
        return self._zxy_real_channel_bool

    @zxy_real_channel_bool.setter
    def zxy_real_channel_bool(self, val):
        self.setter_validator("zxy_real_channel_bool", val)

    @property
    def zxy_real_channel(self):
        return self._zxy_real_channel

    @zxy_real_channel.setter
    def zxy_real_channel(self, val):
        self.setter_validator("zxy_real_channel", val, fun=self._uuid_promoter)

    @property
    def zxy_real_uncertainty(self):
        return self._zxy_real_uncertainty

    @zxy_real_uncertainty.setter
    def zxy_real_uncertainty(self, val):
        self.setter_validator("zxy_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zxy_imag_channel_bool(self):
        return self._zxy_imag_channel_bool

    @zxy_imag_channel_bool.setter
    def zxy_imag_channel_bool(self, val):
        self.setter_validator("zxy_imag_channel_bool", val)

    @property
    def zxy_imag_channel(self):
        return self._zxy_imag_channel

    @zxy_imag_channel.setter
    def zxy_imag_channel(self, val):
        self.setter_validator("zxy_imag_channel", val, fun=self._uuid_promoter)

    @property
    def zxy_imag_uncertainty(self):
        return self._zxy_imag_uncertainty

    @zxy_imag_uncertainty.setter
    def zxy_imag_uncertainty(self, val):
        self.setter_validator("zxy_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zyx_real_channel_bool(self):
        return self._zyx_real_channel_bool

    @zyx_real_channel_bool.setter
    def zyx_real_channel_bool(self, val):
        self.setter_validator("zyx_real_channel_bool", val)

    @property
    def zyx_real_channel(self):
        return self._zyx_real_channel

    @zyx_real_channel.setter
    def zyx_real_channel(self, val):
        self.setter_validator("zyx_real_channel", val, fun=self._uuid_promoter)

    @property
    def zyx_real_uncertainty(self):
        return self._zyx_real_uncertainty

    @zyx_real_uncertainty.setter
    def zyx_real_uncertainty(self, val):
        self.setter_validator("zyx_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zyx_imag_channel_bool(self):
        return self._zyx_imag_channel_bool

    @zyx_imag_channel_bool.setter
    def zyx_imag_channel_bool(self, val):
        self.setter_validator("zyx_imag_channel_bool", val)

    @property
    def zyx_imag_channel(self):
        return self._zyx_imag_channel

    @zyx_imag_channel.setter
    def zyx_imag_channel(self, val):
        self.setter_validator("zyx_imag_channel", val, fun=self._uuid_promoter)

    @property
    def zyx_imag_uncertainty(self):
        return self._zyx_imag_uncertainty

    @zyx_imag_uncertainty.setter
    def zyx_imag_uncertainty(self, val):
        self.setter_validator("zyx_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zyy_real_channel_bool(self):
        return self._zyy_real_channel_bool

    @zyy_real_channel_bool.setter
    def zyy_real_channel_bool(self, val):
        self.setter_validator("zyy_real_channel_bool", val)

    @property
    def zyy_real_channel(self):
        return self._zyy_real_channel

    @zyy_real_channel.setter
    def zyy_real_channel(self, val):
        self.setter_validator("zyy_real_channel", val, fun=self._uuid_promoter)

    @property
    def zyy_real_uncertainty(self):
        return self._zyy_real_uncertainty

    @zyy_real_uncertainty.setter
    def zyy_real_uncertainty(self, val):
        self.setter_validator("zyy_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def zyy_imag_channel_bool(self):
        return self._zyy_imag_channel_bool

    @zyy_imag_channel_bool.setter
    def zyy_imag_channel_bool(self, val):
        self.setter_validator("zyy_imag_channel_bool", val)

    @property
    def zyy_imag_channel(self):
        return self._zyy_imag_channel

    @zyy_imag_channel.setter
    def zyy_imag_channel(self, val):
        self.setter_validator("zyy_imag_channel", val, fun=self._uuid_promoter)

    @property
    def zyy_imag_uncertainty(self):
        return self._zyy_imag_uncertainty

    @zyy_imag_uncertainty.setter
    def zyy_imag_uncertainty(self, val):
        self.setter_validator("zyy_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def background_conductivity(self):
        return self._background_conductivity

    @background_conductivity.setter
    def background_conductivity(self, val):
        self.setter_validator("background_conductivity", val, fun=self._uuid_promoter)
