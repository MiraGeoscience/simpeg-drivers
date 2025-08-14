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
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions, EMDataMixin


class TipperForwardOptions(EMDataMixin, BaseForwardOptions):
    """
    Tipper forward options.

    :param txz_real_channel_bool: Boolean for txz real channel.
    :param txz_imag_channel_bool: Boolean for txz imaginary channel.
    :param tyz_real_channel_bool: Boolean for tyz real channel.
    :param tyz_imag_channel_bool: Boolean for tyz imaginary channel.
    :param background_conductivity: Background conductivity model.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Tipper Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tipper_forward.ui.json"

    title: str = "Tipper Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "tipper"

    data_object: TipperReceivers
    txz_real_channel_bool: bool | None = None
    txz_imag_channel_bool: bool | None = None
    tyz_real_channel_bool: bool | None = None
    tyz_imag_channel_bool: bool | None = None
    background_conductivity: float | FloatData
    model_type: str = "Conductivity (S/m)"


class TipperInversionOptions(EMDataMixin, BaseInversionOptions):
    """
    Tipper Inversion options.

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
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tipper_inversion.ui.json"

    title: str = "Tipper Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "tipper"

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
