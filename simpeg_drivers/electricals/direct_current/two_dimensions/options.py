# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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
from simpeg_drivers.electricals.base_2d import Base2DOptions, Conductivity2DModelOptions
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions


class DC2DForwardOptions(BaseForwardOptions, Base2DOptions):
    """
    Direct Current 2D forward options.

    :param potential_channel_bool: Potential channel boolean.
    """

    name: ClassVar[str] = "Direct Current 2D Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_2d_forward.ui.json"
    )

    title: str = "Direct Current 2D Forward"
    icon: str = "PotentialElectrode"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 2d"

    potential_channel_bool: bool = True
    models: Conductivity2DModelOptions


class DC2DInversionOptions(BaseInversionOptions, Base2DOptions):
    """
    Direct Current 2D inversion options.

    :param potential_channel: Potential data channel.
    :param potential_uncertainty: Potential data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    """

    name: ClassVar[str] = "Direct Current 2D Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_2d_inversion.ui.json"
    )
    icon: str = "PotentialElectrode"
    title: str = "Direct Current 2D Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 2d"

    potential_channel: FloatData
    potential_uncertainty: float | FloatData | None = None
    models: Conductivity2DModelOptions
