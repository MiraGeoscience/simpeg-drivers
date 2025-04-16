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


class GravityForwardOptions(BaseForwardOptions):
    """
    Gravity forward options.

    :param gx_channel_bool: gx channel boolean.
    :param gy_channel_bool: gy channel boolean.
    :param gz_channel_bool: gz channel boolean.
    :param gxx_channel_bool: gxx channel boolean.
    :param gxy_channel_bool: gxy channel boolean.
    :param gxz_channel_bool: gxz channel boolean.
    :param gyy_channel_bool: gyy channel boolean.
    :param gyz_channel_bool: gyz channel boolean.
    :param gzz_channel_bool: gzz channel boolean.
    """

    name: ClassVar[str] = "Gravity Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/gravity_forward.ui.json"

    title: str = "Gravity Forward"
    physical_property: str = "density"
    inversion_type: str = "gravity"

    gx_channel_bool: bool = False
    gy_channel_bool: bool = False
    gz_channel_bool: bool = True
    guv_channel_bool: bool = False
    gxx_channel_bool: bool = False
    gxy_channel_bool: bool = False
    gxz_channel_bool: bool = False
    gyy_channel_bool: bool = False
    gyz_channel_bool: bool = False
    gzz_channel_bool: bool = False


class GravityInversionOptions(BaseInversionOptions):
    """
    Gravity inversion options.

    :param gx_channel: gx channel.
    :param gy_channel: gy channel.
    :param gz_channel: gz channel.
    :param gxx_channel: gxx channel.
    :param gxy_channel: gxy channel.
    :param gxz_channel: gxz channel.
    :param gyy_channel: gyy channel.
    :param gyz_channel: gyz channel.
    :param gzz_channel: gzz channel.
    :param gx_uncertainty: gx uncertainty.
    :param gy_uncertainty: gy uncertainty.
    :param gz_uncertainty: gz uncertainty.
    :param gxx_uncertainty: gxx uncertainty.
    :param gxy_uncertainty: gxy uncertainty.
    :param gxz_uncertainty: gxz uncertainty.
    :param gyy_uncertainty: gyy uncertainty.
    :param gyz_uncertainty: gyz uncertainty.
    :param gzz_uncertainty: gzz uncertainty.
    """

    default_ui_json: ClassVar[Path] = assets_path() / "uijson/gravity_inversion.ui.json"
    name: ClassVar[str] = "Gravity Inversion"

    title: str = "Gravity Inversion"
    physical_property: str = "density"
    inversion_type: str = "gravity"

    gx_channel: FloatData | None = None
    gy_channel: FloatData | None = None
    gz_channel: FloatData | None = None
    guv_channel: FloatData | None = None
    gxx_channel: FloatData | None = None
    gxy_channel: FloatData | None = None
    gxz_channel: FloatData | None = None
    gyy_channel: FloatData | None = None
    gyz_channel: FloatData | None = None
    gzz_channel: FloatData | None = None
    gx_uncertainty: FloatData | float | None = None
    gy_uncertainty: FloatData | float | None = None
    gz_uncertainty: FloatData | float | None = None
    guv_uncertainty: FloatData | float | None = None
    gxx_uncertainty: FloatData | float | None = None
    gxy_uncertainty: FloatData | float | None = None
    gxz_uncertainty: FloatData | float | None = None
    gyy_uncertainty: FloatData | float | None = None
    gyz_uncertainty: FloatData | float | None = None
    gzz_uncertainty: FloatData | float | None = None
