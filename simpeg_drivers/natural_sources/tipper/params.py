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
from typing import ClassVar

from geoh5py.data import FloatData
from geoh5py.groups import PropertyGroup
from geoh5py.objects import TipperReceivers

from simpeg_drivers import assets_path
from simpeg_drivers.params import BaseForwardData, BaseInversionData


class TipperForwardParams(BaseForwardData):
    """
    Parameter class for magnetotelluric->conductivity simulation.

    :param txz_real_channel_bool: Boolean for txz real channel.
    :param txz_imag_channel_bool: Boolean for txz imaginary channel.
    :param tyz_real_channel_bool: Boolean for tyz real channel.
    :param tyz_imag_channel_bool: Boolean for tyz imaginary channel.
    :param background_conductivity: Background conductivity model.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Tipper Forward"
    title: ClassVar[str] = "Tipper Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tipper_forward.ui.json"

    inversion_type: str = "tipper"
    physical_property: str = "conductivity"

    data_object: TipperReceivers
    txz_real_channel_bool: bool | None = None
    txz_imag_channel_bool: bool | None = None
    tyz_real_channel_bool: bool | None = None
    tyz_imag_channel_bool: bool | None = None
    background_conductivity: float | FloatData
    model_type: str = "Conductivity (S/m)"

    @property
    def channels(self) -> list[str]:
        return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]

    def property_group_data(self, property_group: PropertyGroup):
        """
        Return dictionary of channel/data.

        :param property_group: Property group uid
        """
        _ = property_group
        frequencies = self.data_object.channels
        return {k: None for k in frequencies}

    def data(self, component: str):
        """Returns array of data for chosen data component."""
        property_group = self.data_channel(component)
        return self.property_group_data(property_group)

    def uncertainty(self, component: str) -> float:
        """Returns uncertainty for chosen data component."""
        uid = self.uncertainty_channel(component)
        return self.property_group_data(uid)


class TipperInversionParams(BaseInversionData):
    """
    Parameter class for magnetotelluric->conductivity inversion.

    :param txz_real_channel: Real component of Txz tipper data.
    :param txz_real_uncertainty: Real component of Txz tipper uncertainty.
    :param txz_imag_channel: Imaginary component of Txz tipper data.
    :param txz_imag_uncertainty: Imaginary component of Txz tipper uncertainty.
    :param tyz_real_channel: Real component of Tyz tipper data.
    :param tyz_real_uncertainty: Real component of Tyz tipper uncertainty.
    :param tyz_imag_channel: Imaginary component of Tyz tipper data.
    :param tyz_imag_uncertainty: Imaginary component of Tyz tipper uncertainty.
    :param background_conductivity: Background conductivity model.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Tipper Inversion"
    title: ClassVar[str] = "Tipper Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tipper_inversion.ui.json"

    inversion_type: str = "tipper"
    physical_property: str = "conductivity"

    data_object: TipperReceivers
    txz_real_channel: PropertyGroup | None = None
    txz_real_uncertainty: PropertyGroup | None = None
    txz_imag_channel: PropertyGroup | None = None
    txz_imag_uncertainty: PropertyGroup | None = None
    tyz_real_channel: PropertyGroup | None = None
    tyz_real_uncertainty: PropertyGroup | None = None
    tyz_imag_channel: PropertyGroup | None = None
    tyz_imag_uncertainty: PropertyGroup | None = None
    background_conductivity: float | FloatData
    model_type: str = "Conductivity (S/m)"

    @property
    def channels(self) -> list[str]:
        return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]

    def data_channel(self, component: str):
        """Return uuid of data channel."""
        return getattr(self, "_".join([component, "channel"]), None)

    def uncertainty_channel(self, component: str):
        """Return uuid of uncertainty channel."""
        return getattr(self, "_".join([component, "uncertainty"]), None)

    def property_group_data(self, property_group: PropertyGroup):
        """
        Return dictionary of channel/data.

        :param property_group: Property group uid
        """
        data = {}
        frequencies = self.data_object.channels
        group = next(
            k for k in self.data_object.property_groups if k.uid == property_group.uid
        )
        property_names = [self.geoh5.get_entity(p)[0].name for p in group.properties]
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
