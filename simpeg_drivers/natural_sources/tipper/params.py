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


class TipperParams(InversionBaseParams):
    """
    Parameter class for magnetotelluric->conductivity inversion.
    """

    _physical_property = "conductivity"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._inversion_type = "tipper"
        self._validations = validations
        self._txz_real_channel_bool = None
        self._txz_real_channel = None
        self._txz_real_uncertainty = None
        self._txz_imag_channel_bool = None
        self._txz_imag_channel = None
        self._txz_imag_uncertainty = None
        self._tyz_real_channel_bool = None
        self._tyz_real_channel = None
        self._tyz_real_uncertainty = None
        self._tyz_imag_channel_bool = None
        self._tyz_imag_channel = None
        self._tyz_imag_uncertainty = None
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
    def txz_real_channel_bool(self):
        return self._txz_real_channel_bool

    @txz_real_channel_bool.setter
    def txz_real_channel_bool(self, val):
        self.setter_validator("txz_real_channel_bool", val)

    @property
    def txz_real_channel(self):
        return self._txz_real_channel

    @txz_real_channel.setter
    def txz_real_channel(self, val):
        self.setter_validator("txz_real_channel", val, fun=self._uuid_promoter)

    @property
    def txz_real_uncertainty(self):
        return self._txz_real_uncertainty

    @txz_real_uncertainty.setter
    def txz_real_uncertainty(self, val):
        self.setter_validator("txz_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def txz_imag_channel_bool(self):
        return self._txz_imag_channel_bool

    @txz_imag_channel_bool.setter
    def txz_imag_channel_bool(self, val):
        self.setter_validator("txz_imag_channel_bool", val)

    @property
    def txz_imag_channel(self):
        return self._txz_imag_channel

    @txz_imag_channel.setter
    def txz_imag_channel(self, val):
        self.setter_validator("txz_imag_channel", val, fun=self._uuid_promoter)

    @property
    def txz_imag_uncertainty(self):
        return self._txz_imag_uncertainty

    @txz_imag_uncertainty.setter
    def txz_imag_uncertainty(self, val):
        self.setter_validator("txz_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def tyz_real_channel_bool(self):
        return self._tyz_real_channel_bool

    @tyz_real_channel_bool.setter
    def tyz_real_channel_bool(self, val):
        self.setter_validator("tyz_real_channel_bool", val)

    @property
    def tyz_real_channel(self):
        return self._tyz_real_channel

    @tyz_real_channel.setter
    def tyz_real_channel(self, val):
        self.setter_validator("tyz_real_channel", val, fun=self._uuid_promoter)

    @property
    def tyz_real_uncertainty(self):
        return self._tyz_real_uncertainty

    @tyz_real_uncertainty.setter
    def tyz_real_uncertainty(self, val):
        self.setter_validator("tyz_real_uncertainty", val, fun=self._uuid_promoter)

    @property
    def tyz_imag_channel_bool(self):
        return self._tyz_imag_channel_bool

    @tyz_imag_channel_bool.setter
    def tyz_imag_channel_bool(self, val):
        self.setter_validator("tyz_imag_channel_bool", val)

    @property
    def tyz_imag_channel(self):
        return self._tyz_imag_channel

    @tyz_imag_channel.setter
    def tyz_imag_channel(self, val):
        self.setter_validator("tyz_imag_channel", val, fun=self._uuid_promoter)

    @property
    def tyz_imag_uncertainty(self):
        return self._tyz_imag_uncertainty

    @tyz_imag_uncertainty.setter
    def tyz_imag_uncertainty(self, val):
        self.setter_validator("tyz_imag_uncertainty", val, fun=self._uuid_promoter)

    @property
    def background_conductivity(self):
        return self._background_conductivity

    @background_conductivity.setter
    def background_conductivity(self, val):
        self.setter_validator("background_conductivity", val, fun=self._uuid_promoter)
