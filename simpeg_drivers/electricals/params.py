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

from geoh5py.data import DataAssociationEnum, ReferencedData
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class LineSelectionOptions(BaseModel):
    """
    Line selection parameters for 2D inversions.

    :param line_object: Reference data categorizing survey by line ids.
    :param line_id: Line identifier for simulation/inversion.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    line_object: ReferencedData
    line_id: int = 1

    @field_validator("line_object", mode="before")
    @classmethod
    def validate_cell_association(cls, value):
        if value.association is not DataAssociationEnum.CELL:
            raise ValueError("Line identifier must be associated with cells.")
        return value

    @model_validator(mode="after")
    def line_id_referenced(self):
        if self.line_id not in self.line_object.values:
            raise ValueError("Line id isn't referenced in the line object.")
        return self


class DrapeModelOptions(BaseModel):
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


class FileControlOptions(BaseModel):
    """
    File control parameters for pseudo 3D simulations.

    :param files_only: Boolean to only write files.
    :param cleanup: Boolean to cleanup files.
    """

    files_only: bool = False
    cleanup: bool = True
