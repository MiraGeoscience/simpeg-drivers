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


class DC3DForwardOptions(BaseForwardOptions):
    """
    Direct Current 3D forward options.

    :param potential_channel_bool: Potential channel boolean.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 3D Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_3d_forward.ui.json"
    )

    title: str = "Direct Current 3D Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 3d"

    potential_channel_bool: bool = True
    model_type: str = "Conductivity (S/m)"


class DC3DInversionOptions(BaseInversionOptions):
    """
    Direct Current 3D inversion options.

    :param potential_channel: Potential data channel.
    :param potential_uncertainty: Potential data uncertainty channel.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 3D Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_3d_inversion.ui.json"
    )

    title: str = "Direct Current 3D Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 3d"

    potential_channel: FloatData
    potential_uncertainty: float | FloatData | None = None
    model_type: str = "Conductivity (S/m)"
