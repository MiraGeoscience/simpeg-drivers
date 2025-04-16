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

from geoh5py.data import DataAssociationEnum, FloatData, ReferencedData
from geoh5py.objects import DrapeModel
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    DrapeModelOptions,
    LineSelectionOptions,
)


class DC2DForwardOptions(BaseForwardOptions):
    """
    Direct Current 2D forward options.

    :param potential_channel_bool: Potential channel boolean.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 2D Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_2d_forward.ui.json"
    )

    title: str = "Direct Current 2D Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 2d"

    potential_channel_bool: bool = True
    line_selection: LineSelectionOptions
    mesh: DrapeModel | None = None
    drape_model: DrapeModelOptions
    model_type: str = "Conductivity (S/m)"


class DC2DInversionOptions(BaseInversionOptions):
    """
    Direct Current 2D inversion options.

    :param potential_channel: Potential data channel.
    :param potential_uncertainty: Potential data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 2D Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_2d_inversion.ui.json"
    )

    title: str = "Direct Current 2D Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current 2d"

    potential_channel: FloatData
    potential_uncertainty: float | FloatData | None = None
    line_selection: LineSelectionOptions
    mesh: DrapeModel | None = None
    drape_model: DrapeModelOptions
    model_type: str = "Conductivity (S/m)"
    length_scale_y: None = None
    y_norm: None = None
