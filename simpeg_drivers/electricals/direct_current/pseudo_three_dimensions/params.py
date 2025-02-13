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

from geoh5py.data import FloatData
from geoh5py.objects import Octree, PotentialElectrode

from simpeg_drivers import assets_path
from simpeg_drivers.electricals.params import (
    DrapeModelData,
    FileControlData,
    LineSelectionData,
)
from simpeg_drivers.params import BaseForwardData, BaseInversionData


class DCBatch2DForwardParams(BaseForwardData):
    """
    Direct Current batch 2D forward options.

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
        assets_path() / "uijson/direct_current_batch2d_forward.ui.json"
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


class DCBatch2DInversionParams(BaseInversionData):
    """
    Direct Current batch 2D Inversion options.

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
        assets_path() / "uijson/direct_current_batch2d_inversion.ui.json"
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
