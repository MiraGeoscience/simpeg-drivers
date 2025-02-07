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

from copy import deepcopy
from typing import ClassVar

from geoh5py.data import FloatData
from geoh5py.objects import Octree, PotentialElectrode

from simpeg_drivers import assets_path
from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.constants import (
    default_ui_json,
    forward_defaults,
    inversion_defaults,
    validations,
)
from simpeg_drivers.electricals.params import (
    BasePseudo3DParams,
    DrapeModelData,
    FileControlData,
    LineSelectionData,
)
from simpeg_drivers.params import BaseForwardData, BaseInversionData


class DirectCurrentPseudo3DForwardParams(BaseForwardData):
    """
    Parameter class for three dimensional direct current forward simulation.

    :param data_object: DC survey object.
    :param potential_channel_bool: Potential channel boolean.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters common to all 2D simulations.
    :param model_type: Specify whether the models are provided in resistivity
        or conductivity.
    :param file_control: File control parameters.
    """

    name: ClassVar[str] = "Direct Current Pseudo 3D Forward"
    title: ClassVar[str] = "Direct Current (DC) 2D Batch Forward"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/direct_current_pseudo3d_forward.ui.json"
    )

    inversion_type: str = "direct current pseudo 3d"
    physical_property: str = "conductivity"

    data_object: PotentialElectrode
    potential_channel_bool: bool = True
    line_selection: LineSelectionData
    mesh: Octree | None = None
    drape_model: DrapeModelData = DrapeModelData()
    model_type: str = "Conductivity (S/m)"
    file_control: FileControlData = FileControlData()


class DirectCurrentPseudo3DInversionParams(BaseInversionData):
    """
    Parameter class for three dimensional direct current inversion.

    :param data_object: DC survey object.
    :param potential_channel: Potential data channel.
    :param potential_uncertainty: Potential data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters.
    :param model_type: Specify whether the models are provided in resistivity
        or conductivity.
    :param file_control: File control parameters.
    :param length_scale_y: Inactive length scale for y direction.
    :param y_norm: Inactive y normalization factor.
    """

    name: ClassVar[str] = "Direct Current Pseudo 3D Inversion"
    title: ClassVar[str] = "Direct Current (DC) 2D Batch Inversion"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/direct_current_pseudo3d_inversion.ui.json"
    )

    inversion_type: str = "direct current pseudo 3d"
    physical_property: str = "conductivity"

    data_object: PotentialElectrode
    potential_channel: FloatData
    potential_uncertainty: float | FloatData
    line_selection: LineSelectionData
    mesh: Octree | None = None
    drape_model: DrapeModelData = DrapeModelData()
    model_type: str = "Conductivity (S/m)"
    file_control: FileControlData = FileControlData()
    length_scale_y: None = None
    y_norm: None = None


class DirectCurrentPseudo3DParams(BasePseudo3DParams):
    """
    Parameter class for electrical->conductivity inversion.
    """

    _physical_property = "conductivity"
    _inversion_type = "direct current 3d"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._validations = validations
        self._potential_channel_bool = None
        self._potential_channel = None
        self._potential_uncertainty = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def line_selection(self):
        return LineSelectionData(line_object=self.line_object, line_id=1)

    @property
    def potential_channel_bool(self):
        return self._potential_channel_bool

    @potential_channel_bool.setter
    def potential_channel_bool(self, val):
        self.setter_validator("potential_channel_bool", val)

    @property
    def potential_channel(self):
        return self._potential_channel

    @potential_channel.setter
    def potential_channel(self, val):
        self.setter_validator("potential_channel", val, fun=self._uuid_promoter)

    @property
    def potential_uncertainty(self):
        return self._potential_uncertainty

    @potential_uncertainty.setter
    def potential_uncertainty(self, val):
        self.setter_validator("potential_uncertainty", val, fun=self._uuid_promoter)
