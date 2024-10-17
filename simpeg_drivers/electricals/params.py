# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import numpy as np
from geoh5py.data import Data, DataAssociationEnum

from simpeg_drivers import InversionBaseParams
from simpeg_drivers.utils.utils import get_drape_model


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
