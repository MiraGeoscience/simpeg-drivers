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

from pathlib import Path
from typing import ClassVar, TypeAlias

from geoh5py.groups import PropertyGroup
from geoh5py.objects import (
    AirborneTEMReceivers,
    LargeLoopGroundTEMReceivers,
    MovingLoopGroundTEMReceivers,
)

from simpeg_drivers import assets_path
from simpeg_drivers.params import BaseForwardData, BaseInversionData


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class TimeDomainElectromagneticsForwardParams(BaseForwardData):
    """
    Parameter class for Time-domain Electromagnetic (TEM) -> conductivity forward simulation.

    :param z_channel_bool: Z-component data channel boolean.
    :param z_channel_uncertainty: Z-component data channel uncertainty.
    :param x_channel_bool: X-component data channel boolean.
    :param x_channel_uncertainty: X-component data channel uncertainty.
    :param y_channel_bool: Y-component data channel boolean.
    :param y_channel_uncertainty: Y-component data channel uncertainty.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    title: ClassVar[str] = "Time-domain EM (TEM) Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_forward.ui.json"

    inversion_type: str = "tdem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel_bool: bool
    x_channel_bool: bool
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]

    def property_group_data(self, property_group: PropertyGroup):
        """
        Return dictionary of channel/data.

        :param property_group: Property group containing em data.
        """
        _ = property_group
        channels = self.data_object.channels
        return {k: None for k in channels}

    def data(self, component: str):
        """Returns array of data for chosen data component."""
        property_group = self.data_channel(component)
        return self.property_group_data(property_group)

    def uncertainty(self, component: str) -> float:
        """Returns uncertainty for chosen data component."""
        uid = self.uncertainty_channel(component)
        return self.property_group_data(uid)


class TimeDomainElectromagneticsInversionParams(BaseInversionData):
    """
    Parameter class for Time-domain Electromagnetic (TEM) -> conductivity inversion.

    :param z_channel: Z-component data channel.
    :param z_uncertainty: Z-component data channel uncertainty.
    :param x_channel: X-component data channel.
    :param x_uncertainty: X-component data channel uncertainty.
    :param y_channel: Y-component data channel.
    :param y_uncertainty: Y-component data channel uncertainty.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    title: ClassVar[str] = "Time-domain EM (TEM) Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_inversion.ui.json"

    inversion_type: str = "tdem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None
    x_channel: PropertyGroup | None = None
    x_uncertainty: PropertyGroup | None = None
    y_channel: PropertyGroup | None = None
    y_uncertainty: PropertyGroup | None = None
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]

    def property_group_data(self, property_group: PropertyGroup):
        """
        Return dictionary of channel/data.

        :param property_group: Property group containing TEM data.
        """
        data = {}
        channels = self.data_object.channels
        group = self.data_object.fetch_property_group(name=property_group.name)
        property_names = [self.geoh5.get_entity(p)[0].name for p in group.properties]
        properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
        for i, f in enumerate(channels):
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


# class TimeDomainElectromagneticsParams(InversionBaseParams):
#     """
#     Parameter class for Time-domain Electromagnetic (TEM) -> conductivity inversion.
#     """
#
#     _physical_property = "conductivity"
#
#     def __init__(self, input_file=None, forward_only=False, **kwargs):
#         self._default_ui_json = deepcopy(default_ui_json)
#         self._forward_defaults = deepcopy(forward_defaults)
#         self._inversion_defaults = deepcopy(inversion_defaults)
#         self._inversion_type = "tdem"
#         self._validations = validations
#         self._data_units = "dB/dt (T/s)"
#         self._z_channel_bool = None
#         self._z_channel = None
#         self._z_uncertainty = None
#         self._x_channel_bool = None
#         self._x_channel = None
#         self._x_uncertainty = None
#         self._y_channel_bool = None
#         self._y_channel = None
#         self._y_uncertainty = None
#
#         self._model_type = "Conductivity (S/m)"
#
#         super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)
#
#     def data_channel(self, component: str):
#         """Return uuid of data channel."""
#         return getattr(self, "_".join([component, "channel"]), None)
#
#     @property
#     def data_units(self):
#         return self._data_units
#
#     @data_units.setter
#     def data_units(self, val):
#         self.setter_validator("data_units", val)
#
#     def uncertainty_channel(self, component: str):
#         """Return uuid of uncertainty channel."""
#         return getattr(self, "_".join([component, "uncertainty"]), None)
#
#     def property_group_data(self, property_group: UUID):
#         data = {}
#         channels = self.data_object.channels
#         if self.forward_only:
#             return {k: None for k in channels}
#         else:
#             group = self.data_object.find_or_create_property_group(
#                 name=property_group.name
#             )
#             property_names = [
#                 self.geoh5.get_entity(p)[0].name for p in group.properties
#             ]
#             properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
#             for i, f in enumerate(channels):
#                 try:
#                     f_ind = property_names.index(
#                         next(k for k in property_names if f"{f:.2e}" in k)
#                     )  # Safer if data was saved with geoapps naming convention
#                     data[f] = properties[f_ind]
#                 except StopIteration:
#                     data[f] = properties[i]  # in case of other naming conventions
#
#             return data
#
#     @property
#     def model_type(self):
#         """Model units."""
#         return self._model_type
#
#     @model_type.setter
#     def model_type(self, val):
#         self.setter_validator("model_type", val)
#
#     @property
#     def unit_conversion(self):
#         """Return time unit conversion factor."""
#         conversion = {
#             "Seconds (s)": 1.0,
#             "Milliseconds (ms)": 1e-3,
#             "Microseconds (us)": 1e-6,
#         }
#         return conversion[self.data_object.unit]
#
#     def data(self, component: str):
#         """Returns array of data for chosen data component."""
#         property_group = self.data_channel(component)
#         return self.property_group_data(property_group)
#
#     def uncertainty(self, component: str) -> float:
#         """Returns uncertainty for chosen data component."""
#         uid = self.uncertainty_channel(component)
#         return self.property_group_data(uid)
#
#     @property
#     def z_channel_bool(self):
#         return self._z_channel_bool
#
#     @z_channel_bool.setter
#     def z_channel_bool(self, val):
#         self.setter_validator("z_channel_bool", val)
#
#     @property
#     def z_channel(self):
#         return self._z_channel
#
#     @z_channel.setter
#     def z_channel(self, val):
#         self.setter_validator("z_channel", val, fun=self._uuid_promoter)
#
#     @property
#     def z_uncertainty(self):
#         return self._z_uncertainty
#
#     @z_uncertainty.setter
#     def z_uncertainty(self, val):
#         self.setter_validator("z_uncertainty", val, fun=self._uuid_promoter)
#
#     @property
#     def x_channel_bool(self):
#         return self._x_channel_bool
#
#     @x_channel_bool.setter
#     def x_channel_bool(self, val):
#         self.setter_validator("x_channel_bool", val)
#
#     @property
#     def x_channel(self):
#         return self._x_channel
#
#     @x_channel.setter
#     def x_channel(self, val):
#         self.setter_validator("x_channel", val, fun=self._uuid_promoter)
#
#     @property
#     def x_uncertainty(self):
#         return self._x_uncertainty
#
#     @x_uncertainty.setter
#     def x_uncertainty(self, val):
#         self.setter_validator("x_uncertainty", val, fun=self._uuid_promoter)
#
#     @property
#     def y_channel_bool(self):
#         return self._y_channel_bool
#
#     @y_channel_bool.setter
#     def y_channel_bool(self, val):
#         self.setter_validator("y_channel_bool", val)
#
#     @property
#     def y_channel(self):
#         return self._y_channel
#
#     @y_channel.setter
#     def y_channel(self, val):
#         self.setter_validator("y_channel", val, fun=self._uuid_promoter)
#
#     @property
#     def y_uncertainty(self):
#         return self._y_uncertainty
#
#     @y_uncertainty.setter
#     def y_uncertainty(self, val):
#         self.setter_validator("y_uncertainty", val, fun=self._uuid_promoter)
