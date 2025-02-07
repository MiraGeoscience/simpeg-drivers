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

from geoh5py.data import Data, DataAssociationEnum, ReferencedData
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from simpeg_drivers.params import InversionBaseParams


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


class FileControlData(BaseModel):
    """
    File control parameters for pseudo 3D simulations.

    :param files_only: Boolean to only write files.
    :param cleanup: Boolean to cleanup files.
    """

    files_only: bool = False
    cleanup: bool = True


class Core2DParams(InversionBaseParams):
    """
    Core parameter class for 2D electrical->conductivity inversion.
    """

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._line_object = None
        self._u_cell_size: float = 25.0
        self._v_cell_size: float = 25.0
        self._depth_core: float = 100.0
        self._horizontal_padding: float = 100.0
        self._vertical_padding: float = 100.0
        self._expansion_factor: float = 100.0
        self._model_type = "Conductivity (S/m)"

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def line_object(self):
        """ReferenceData entity containing line information on poles."""
        return self._line_object

    @line_object.setter
    def line_object(self, val):
        self._line_object = val

        if isinstance(val, Data) and val.association is not DataAssociationEnum.CELL:
            raise ValueError("Line identifier must be associated with cells.")

    @property
    def model_type(self):
        """Model units."""
        return self._model_type

    @model_type.setter
    def model_type(self, val):
        self.setter_validator("model_type", val)

    @property
    def u_cell_size(self):
        """"""
        return self._u_cell_size

    @u_cell_size.setter
    def u_cell_size(self, value):
        self.setter_validator("u_cell_size", value)

    @property
    def v_cell_size(self):
        """"""
        return self._v_cell_size

    @v_cell_size.setter
    def v_cell_size(self, value):
        self.setter_validator("v_cell_size", value)

    @property
    def depth_core(self):
        """"""
        return self._depth_core

    @depth_core.setter
    def depth_core(self, value):
        self.setter_validator("depth_core", value)

    @property
    def horizontal_padding(self):
        """"""
        return self._horizontal_padding

    @horizontal_padding.setter
    def horizontal_padding(self, value):
        self.setter_validator("horizontal_padding", value)

    @property
    def vertical_padding(self):
        """"""
        return self._vertical_padding

    @vertical_padding.setter
    def vertical_padding(self, value):
        self.setter_validator("vertical_padding", value)

    @property
    def expansion_factor(self):
        """"""
        return self._expansion_factor

    @expansion_factor.setter
    def expansion_factor(self, value):
        self.setter_validator("expansion_factor", value)


class Base2DParams(Core2DParams):
    """
    Parameter class for electrical->induced polarization (IP) inversion.
    """

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._line_id = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def line_id(self):
        """Line ID to invert."""
        return self._line_id

    @line_id.setter
    def line_id(self, val):
        self._line_id = val


class BasePseudo3DParams(Core2DParams):
    """
    Base parameter class for pseudo electrical->conductivity inversion.
    """

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._files_only = None
        self._cleanup = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def files_only(self):
        return self._files_only

    @files_only.setter
    def files_only(self, val):
        self.setter_validator("files_only", val)

    @property
    def cleanup(self):
        return self._cleanup

    @cleanup.setter
    def cleanup(self, val):
        self.setter_validator("cleanup", val)
