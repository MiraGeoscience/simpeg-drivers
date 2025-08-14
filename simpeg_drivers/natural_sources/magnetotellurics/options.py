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
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions, EMDataMixin


class MTForwardOptions(EMDataMixin, BaseForwardOptions):
    """
    Magnetotellurics forward options.

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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetotellurics_forward.ui.json"
    )

    title: str = "Magnetotellurics Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "magnetotellurics"

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


class MTInversionOptions(EMDataMixin, BaseInversionOptions):
    """
    Magnetotellurics inversion options.

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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetotellurics_inversion.ui.json"
    )

    title: str = "Magnetotellurics Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "magnetotellurics"

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
