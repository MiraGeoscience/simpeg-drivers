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
from geoh5py.objects import Octree, PotentialElectrode

from simpeg_drivers import assets_path
from simpeg_drivers.electricals.options import (
    FileControlOptions,
)
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    DrapeModelOptions,
    LineSelectionOptions,
)


class DCBatch2DForwardOptions(BaseForwardOptions):
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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_batch2d_forward.ui.json"
    )

    title: str = "Direct Current (DC) 2D Batch Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current pseudo 3d"

    data_object: PotentialElectrode
    potential_channel_bool: bool = True
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
    file_control: FileControlOptions = FileControlOptions()


class DCBatch2DInversionOptions(BaseInversionOptions):
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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/direct_current_batch2d_inversion.ui.json"
    )

    title: str = "Direct Current (DC) 2D Batch Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "direct current pseudo 3d"

    data_object: PotentialElectrode
    potential_channel: FloatData
    potential_uncertainty: float | FloatData
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
    file_control: FileControlOptions = FileControlOptions()
    length_scale_y: None = None
    y_norm: None = None
