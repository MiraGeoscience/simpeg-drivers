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
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.constants import (
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


class InducedPolarizationPseudo3DForwardParams(BaseForwardData):
    """
    Parameter class for three dimensional induced polarization forward simulation.

    :param data_object: DC/IP survey object.
    :param chargeability_channel_bool: Chargeability channel boolean.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters common to all 2D simulations.
    :param model_type: Specify whether the models are provided in resistivity
        or conductivity.
    :param file_control: File control parameters.
    """

    name: ClassVar[str] = "Induced Polarization Pseudo 3D Forward"
    title: ClassVar[str] = "Induced Polarization (IP) 2D Batch Forward"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/induced_polarization_pseudo3d_forward.ui.json"
    )

    inversion_type: str = "induced polarization pseudo 3d"
    physical_property: str = "chargeability"

    data_object: PotentialElectrode
    chargeability_channel_bool: bool = True
    line_selection: LineSelectionData
    mesh: Octree | None = None
    conductivity_model: float | FloatData
    drape_model: DrapeModelData = DrapeModelData()
    file_control: FileControlData = FileControlData()


class InducedPolarizationPseudo3DInversionParams(BaseInversionData):
    """
    Parameter class for three dimensional induced polarization inversion.

    :param data_object: DC/IP survey object.
    :param chargeability_channel: Chargeability data channel.
    :param chargeability_uncertainty: Chargeability data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters common to all 2D simulations.
    :param conductivity_model: Conductivity model.
    :param file_control: File control parameters.
    :param length_scale_y: Inactive length scale for y direction.
    :param y_norm: Inactive y normalization factor.
    """

    name: ClassVar[str] = "Induced Polarization Pseudo 3D Inversion"
    title: ClassVar[str] = "Induced Polarization (IP) 2D Batch Inversion"
    default_ui_json: ClassVar[str] = (
        assets_path() / "uijson/induced_polarization_pseudo3d_inversion.ui.json"
    )

    inversion_type: str = "induced polarization pseudo 3d"
    physical_property: str = "chargeability"

    data_object: PotentialElectrode
    chargeability_channel: FloatData
    chargeability_uncertainty: float | FloatData
    line_selection: LineSelectionData
    mesh: Octree | None = None
    drape_model: DrapeModelData = DrapeModelData()
    conductivity_model: float | FloatData
    lower_bound: float | FloatData | None = 0.0
    file_control: FileControlData = FileControlData()
    length_scale_y: None = None
    y_norm: None = None


class InducedPolarizationPseudo3DParams(BasePseudo3DParams):
    """
    Parameter class for electrical->chargeability inversion.
    """

    _physical_property = "chargeability"
    _inversion_type = "induced polarization pseudo 3d"

    def __init__(self, input_file=None, forward_only=False, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._forward_defaults = deepcopy(forward_defaults)
        self._inversion_defaults = deepcopy(inversion_defaults)
        self._validations = validations
        self._conductivity_model: float | None = 1e-3
        self._chargeability_channel_bool: bool = True
        self._chargeability_channel = None
        self._chargeability_uncertainty = None

        super().__init__(input_file=input_file, forward_only=forward_only, **kwargs)

    @property
    def line_selection(self):
        return LineSelectionData(line_object=self.line_object, line_id=1)

    @property
    def conductivity_model(self):
        return self._conductivity_model

    @conductivity_model.setter
    def conductivity_model(self, value):
        self.setter_validator("conductivity_model", value)

    @property
    def chargeability_channel_bool(self):
        return self._chargeability_channel_bool

    @chargeability_channel_bool.setter
    def chargeability_channel_bool(self, value):
        self.setter_validator("chargeability_channel_bool", value)

    @property
    def chargeability_channel(self):
        return self._chargeability_channel

    @chargeability_channel.setter
    def chargeability_channel(self, value):
        self.setter_validator("chargeability_channel", value)

    @property
    def chargeability_uncertainty(self):
        return self._chargeability_uncertainty

    @chargeability_uncertainty.setter
    def chargeability_uncertainty(self, value):
        self.setter_validator("chargeability_uncertainty", value)
