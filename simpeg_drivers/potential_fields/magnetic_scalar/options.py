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

from simpeg_drivers import assets_path
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions


class MagneticForwardOptions(BaseForwardOptions):
    """
    Magnetic forward options.

    :param tmi_channel_bool: Total magnetic intensity channel boolean.
    :param bx_channel_bool: bx channel boolean.
    :param by_channel_bool: by channel boolean.
    :param bz_channel_bool: bz channel boolean.
    :param bxx_channel_bool: bxx channel boolean.
    :param bxy_channel_bool: bxy channel boolean.
    :param bxz_channel_bool: bxz channel boolean.
    :param byy_channel_bool: byy channel boolean.
    :param byz_channel_bool: byz channel boolean.
    :param bzz_channel_bool: bzz channel boolean.
    """

    name: ClassVar[str] = "Magnetic Scalar Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetic_scalar_forward.ui.json"
    )

    title: str = "Magnetic Scalar Forward"
    physical_property: str = "susceptibility"
    inversion_type: str = "magnetic scalar"

    tmi_channel_bool: bool = True
    bx_channel_bool: bool = False
    by_channel_bool: bool = False
    bz_channel_bool: bool = False
    bxx_channel_bool: bool = False
    bxy_channel_bool: bool = False
    bxz_channel_bool: bool = False
    byy_channel_bool: bool = False
    byz_channel_bool: bool = False
    bzz_channel_bool: bool = False


class MagneticInversionOptions(BaseInversionOptions):
    """
    Magnetic inversion options.

    :param tmi_channel: Total magnetic intensity channel.
    :param bx_channel: bx channel.
    :param by_channel: by channel.
    :param bz_channel: bz channel.
    :param bxx_channel: bxx channel.
    :param bxy_channel: bxy channel.
    :param bxz_channel: bxz channel.
    :param byy_channel: byy channel.
    :param byz_channel: byz channel.
    :param bzz_channel: bzz channel.
    :param tmi_uncertainty: Total magnetic intensity uncertainty.
    :param bx_uncertainty: bx uncertainty.
    :param by_uncertainty: by uncertainty.
    :param bz_uncertainty: bz uncertainty.
    :param bxx_uncertainty: bxx uncertainty.
    :param bxy_uncertainty: bxy uncertainty.
    :param bxz_uncertainty: bxz uncertainty.
    :param byy_uncertainty: byy uncertainty.
    :param byz_uncertainty: byz uncertainty.
    :param bzz_uncertainty: bzz uncertainty.
    :param inducing_field_strength: Inducing field strength.
    :param inducing_field_inclination: Inducing field inclination.
    :param inducing_field_declination: Inducing field declination.
    """

    name: ClassVar[str] = "Magnetic Scalar Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetic_scalar_inversion.ui.json"
    )

    title: str = "Magnetic Scalar Inversion"
    physical_property: str = "susceptibility"
    inversion_type: str = "magnetic scalar"

    tmi_channel: FloatData | None = None
    bx_channel: FloatData | None = None
    by_channel: FloatData | None = None
    bz_channel: FloatData | None = None
    bxx_channel: FloatData | None = None
    bxy_channel: FloatData | None = None
    bxz_channel: FloatData | None = None
    byy_channel: FloatData | None = None
    byz_channel: FloatData | None = None
    bzz_channel: FloatData | None = None
    tmi_uncertainty: float | FloatData | None = None
    bx_uncertainty: float | FloatData | None = None
    by_uncertainty: float | FloatData | None = None
    bz_uncertainty: float | FloatData | None = None
    bxx_uncertainty: float | FloatData | None = None
    bxy_uncertainty: float | FloatData | None = None
    bxz_uncertainty: float | FloatData | None = None
    byy_uncertainty: float | FloatData | None = None
    byz_uncertainty: float | FloatData | None = None
    bzz_uncertainty: float | FloatData | None = None
    inducing_field_strength: float | FloatData
    inducing_field_inclination: float | FloatData
    inducing_field_declination: float | FloatData
    lower_bound: float | FloatData | None = 0.0
