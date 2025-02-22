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
from simpeg_drivers.electricals.params import (
    DrapeModelOptions,
    FileControlOptions,
    LineSelectionOptions,
)
from simpeg_drivers.params import BaseForwardOptions, BaseInversionOptions


class IPBatch2DForwardOptions(BaseForwardOptions):
    """
    Induced Polarization batch 2D forward options.

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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_batch2d_forward.ui.json"
    )

    inversion_type: str = "induced polarization pseudo 3d"
    physical_property: str = "chargeability"

    data_object: PotentialElectrode
    chargeability_channel_bool: bool = True
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    conductivity_model: float | FloatData
    drape_model: DrapeModelOptions = DrapeModelOptions()
    file_control: FileControlOptions = FileControlOptions()


class IPBatch2DInversionOptions(BaseInversionOptions):
    """
    Induced Polarization batch 2D inversion options.

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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_batch2d_inversion.ui.json"
    )

    inversion_type: str = "induced polarization pseudo 3d"
    physical_property: str = "chargeability"

    data_object: PotentialElectrode
    chargeability_channel: FloatData
    chargeability_uncertainty: float | FloatData
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    conductivity_model: float | FloatData
    lower_bound: float | FloatData | None = 0.0
    file_control: FileControlOptions = FileControlOptions()
    length_scale_y: None = None
    y_norm: None = None
