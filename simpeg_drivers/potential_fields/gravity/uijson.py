# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path
from typing import ClassVar
from uuid import UUID

from geoh5py.ui_json.ui_json import BaseUIJson

from simpeg_drivers import assets_path
from simpeg_drivers.uijson import BaseInversionUIJson, CoreUIJson


class GravityForwardUIJson(CoreUIJson):
    default_ui_json: ClassVar[Path] = assets_path / "gravity_forward.ui.json"
    title: str = "Gravity Inversion"
    inversion_type: str = "gravity"

    gx_channel: UUID | None = None
    gy_channel: UUID | None = None
    gz_channel: UUID | None = None
    gxx_channel: UUID | None = None
    gxy_channel: UUID | None = None
    gxz_channel: UUID | None = None
    gyy_channel: UUID | None = None
    gyz_channel: UUID | None = None
    gzz_channel: UUID | None = None
    gx_uncertainty: UUID | float | None = None
    gy_uncertainty: UUID | float | None = None
    gz_uncertainty: UUID | float | None = None
    gxx_uncertainty: UUID | float | None = None
    gxy_uncertainty: UUID | float | None = None
    gxz_uncertainty: UUID | float | None = None
    gyy_uncertainty: UUID | float | None = None
    gyz_uncertainty: UUID | float | None = None
    gzz_uncertainty: UUID | float | None = None


class GravityInversionUIJson(BaseInversionUIJson):
    default_ui_json: ClassVar[Path] = assets_path / "gravity_inversion.ui.json"
    title: str = "Gravity Inversion"
    inversion_type: str = "gravity"

    gx_channel_bool: bool = False
    gy_channel_bool: bool = False
    gz_channel_bool: bool = True
    gxx_channel_bool: bool = False
    gxy_channel_bool: bool = False
    gxz_channel_bool: bool = False
    gyy_channel_bool: bool = False
    gyz_channel_bool: bool = False
    gzz_channel_bool: bool = False
