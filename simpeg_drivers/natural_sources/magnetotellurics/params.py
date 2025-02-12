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
from geoh5py.objects import MTReceivers

from simpeg_drivers import assets_path
from simpeg_drivers.params import BaseForwardData, BaseInversionData, EMDataMixin


class MagnetotelluricsForwardParams(EMDataMixin, BaseForwardData):
    """
    Parameter class for magnetotelluric->conductivity simulation.

    :param zxx_real_channel_bool: Boolean for zxx real channel.
    :param zxx_imag_channel_bool: Boolean for zxx imaginary channel.
    :param zxy_real_channel_bool: Boolean for zxy real channel.
    :param zxy_imag_channel_bool: Boolean for zxy imaginary channel.
    :param zyx_real_channel_bool: Boolean for zyx real channel.
    :param zyx_imag_channel_bool: Boolean for zyx imaginary channel.
    :param zyy_real_channel_bool: Boolean for zyy real channel.
    :param zyy_imag_channel_bool: Boolean for zyy imaginary channel.
    :param background_conductivity: Background conductivity model.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Magnetotellurics Forward"
    title: ClassVar[str] = "Magnetotellurics Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetotellurics_forward.ui.json"
    )

    inversion_type: str = "magnetotellurics"
    physical_property: str = "conductivity"

    data_object: MTReceivers
    zxx_real_channel_bool: bool | None = None
    zxx_imag_channel_bool: bool | None = None
    zxy_real_channel_bool: bool | None = None
    zxy_imag_channel_bool: bool | None = None
    zyx_real_channel_bool: bool | None = None
    zyx_imag_channel_bool: bool | None = None
    zyy_real_channel_bool: bool | None = None
    zyy_imag_channel_bool: bool | None = None
    background_conductivity: float | FloatData
    model_type: str = "Conductivity (S/m)"

    @property
    def channels(self) -> list[str]:
        return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]

    # def property_group_data(self, property_group: PropertyGroup):
    #     """
    #     Return dictionary of channel/data.
    #
    #     :param property_group: Property group uid
    #     """
    #     _ = property_group
    #     frequencies = self.data_object.channels
    #     return {k: None for k in frequencies}
    #
    # def data(self, component: str):
    #     """Returns array of data for chosen data component."""
    #     property_group = self.data_channel(component)
    #     return self.property_group_data(property_group)
    #
    # def uncertainty(self, component: str) -> float:
    #     """Returns uncertainty for chosen data component."""
    #     uid = self.uncertainty_channel(component)
    #     return self.property_group_data(uid)


class MagnetotelluricsInversionParams(EMDataMixin, BaseInversionData):
    """
    Parameter class for magnetotelluric->conductivity inversion.

    :param zxx_real_channel: Real component of Zxx data.
    :param zxx_real_uncertainty: Real component of Zxx uncertainty.
    :param zxx_imag_channel: Imaginary component of Zxx data.
    :param zxx_imag_uncertainty: Imaginary component of Zxx uncertainty.
    :param zxy_real_channel: Real component of Zxy data.
    :param zxy_real_uncertainty: Real component of Zxy uncertainty.
    :param zxy_imag_channel: Imaginary component of Zxy data.
    :param zxy_imag_uncertainty: Imaginary component of Zxy uncertainty.
    :param zyx_real_channel: Real component of Zyx data.
    :param zyx_real_uncertainty: Real component of Zyx uncertainty.
    :param zyx_imag_channel: Imaginary component of Zyx data.
    :param zyx_imag_uncertainty: Imaginary component of Zyx uncertainty.
    :param zyy_real_channel: Real component of Zyy data.
    :param zyy_real_uncertainty: Real component of Zyy uncertainty.
    :param zyy_imag_channel: Imaginary component of Zyy data.
    :param zyy_imag_uncertainty: Imaginary component of Zyy uncertainty.
    :param background_conductivity: Background conductivity model.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Magnetotellurics Inversion"
    title: ClassVar[str] = "Magnetotellurics Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetotellurics_inversion.ui.json"
    )

    inversion_type: str = "magnetotellurics"
    physical_property: str = "conductivity"

    data_object: MTReceivers
    zxx_real_channel: PropertyGroup | None = None
    zxx_real_uncertainty: PropertyGroup | None = None
    zxx_imag_channel: PropertyGroup | None = None
    zxx_imag_uncertainty: PropertyGroup | None = None
    zxy_real_channel: PropertyGroup | None = None
    zxy_real_uncertainty: PropertyGroup | None = None
    zxy_imag_channel: PropertyGroup | None = None
    zxy_imag_uncertainty: PropertyGroup | None = None
    zyx_real_channel: PropertyGroup | None = None
    zyx_real_uncertainty: PropertyGroup | None = None
    zyx_imag_channel: PropertyGroup | None = None
    zyx_imag_uncertainty: PropertyGroup | None = None
    zyy_real_channel: PropertyGroup | None = None
    zyy_real_uncertainty: PropertyGroup | None = None
    zyy_imag_channel: PropertyGroup | None = None
    zyy_imag_uncertainty: PropertyGroup | None = None
    background_conductivity: float | FloatData
    model_type: str = "Conductivity (S/m)"

    # @property
    # def channels(self) -> list[str]:
    #     return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]
    #
    # def property_group_data(self, property_group: PropertyGroup):
    #     """
    #     Return dictionary of channel/data.
    #
    #     :param property_group: Property group uid
    #     """
    #     data = {}
    #     frequencies = self.data_object.channels
    #     if property_group is None:
    #         return {k: None for k in frequencies}
    #     group = next(
    #         k for k in self.data_object.property_groups if k.uid == property_group.uid
    #     )
    #     property_names = [self.geoh5.get_entity(p)[0].name for p in group.properties]
    #     properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
    #     for i, f in enumerate(frequencies):
    #         try:
    #             f_ind = property_names.index(
    #                 next(k for k in property_names if f"{f:.2e}" in k)
    #             )  # Safer if data was saved with geoapps naming convention
    #             data[f] = properties[f_ind]
    #         except StopIteration:
    #             data[f] = properties[i]  # in case of other naming conventions
    #
    #     return data

    #
    # @property
    # def data(self, component: str):
    #     """Returns array of data for chosen data component."""
    #     property_group = self.data_channel(component)
    #     return self.property_group_data(property_group)
    # @property
    # def uncertainty(self, component: str) -> float:
    #     """Returns uncertainty for chosen data component."""
    #     uid = self.uncertainty_channel(component)
    #     return self.property_group_data(uid)
