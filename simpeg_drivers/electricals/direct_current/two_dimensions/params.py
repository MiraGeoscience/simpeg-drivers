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

from typing import ClassVar

from geoh5py.data import DataAssociationEnum, FloatData, ReferencedData
from geoh5py.objects import DrapeModel
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.electricals.params import Base2DParams
from simpeg_drivers.params import BaseForwardData, BaseInversionData

from .constants import (
    validations,
)


class LineSelectionData(BaseModel):
    """
    Line selection parameters for 2D inversions.

    :param line_object: Reference data categorizing survey by line ids.
    :param line_id: Line identifier for simulation/inversion.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    line_object: ReferencedData
    line_id: int

    @field_validator("line_object", mode="before")
    @classmethod
    def validate_cell_association(cls, value):
        if value.association is not DataAssociationEnum.CELL:
            raise ValueError("Line identifier must be associated with cells.")
        return value

    @model_validator(mode="before")
    @classmethod
    def line_id_referenced(cls, model):
        if model["line_id"] not in model["line_object"]():
            raise ValueError("Line id isn't referenced in the line object.")
        return model


class DrapeModelData(BaseModel):
    """
    Drape model parameters for 2D simulation/inversion].

    :param u_cell_size: Horizontal cell size for the drape model.
    :param v_cell_size: Vertical cell size for the drape model.
    :param depth_core: Depth of the core region.
    :param horizontal_padding: Horizontal padding.
    :param vertical_padding: Vertical padding.
    :param expansion_factor: Expansion factor for the drape model.
    """

    u_cell_size: float = 25.0
    v_cell_size: float = 25.0
    depth_core: float = 100.0
    horizontal_padding: float = 100.0
    vertical_padding: float = 100.0
    expansion_factor: float = 100.0


class DirectCurrent2DForwardParams(BaseForwardData):
    """
    Parameter class for two dimensional electrical->conductivity forward simulation.

    :param potential_channel_bool: Potential channel boolean.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 2D Forward"
    title: ClassVar[str] = "Direct Current 2D Forward"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/direct_current_2d_forward.ui.json"
    )

    inversion_type: str = "direct current 2d"
    physical_property: str = "conductivity"

    potential_channel_bool: bool = True
    line_selection: LineSelectionData
    mesh: DrapeModel | None = None
    drape_model: DrapeModelData
    model_type: str = "Conductivity (S/m)"


class DirectCurrent2DInversionParams(BaseInversionData):
    """
    Parameter class for two dimensional electrical->conductivity forward simulation.

    :param potential_channel: Potential data channel.
    :param potential_uncertainty: Potential data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    :param model_type: Specify whether the models are provided in
        resistivity or conductivity.
    """

    name: ClassVar[str] = "Direct Current 2D Inversion"
    title: ClassVar[str] = "Direct Current 2D Inversion"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/direct_current_2d_inversion.ui.json"
    )

    inversion_type: str = "direct current 2d"
    physical_property: str = "conductivity"

    potential_channel: FloatData
    potential_uncertainty: float | FloatData | None = None
    line_selection: LineSelectionData
    mesh: DrapeModel | None = None
    drape_model: DrapeModelData
    model_type: str = "Conductivity (S/m)"
