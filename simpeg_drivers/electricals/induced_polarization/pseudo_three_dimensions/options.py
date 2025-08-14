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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_batch2d_forward.ui.json"
    )

    title: str = "Induced Polarization (IP) 2D Batch Forward"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization pseudo 3d"

    data_object: PotentialElectrode
    chargeability_channel_bool: bool = True
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    conductivity_model: float | FloatData
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
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
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_batch2d_inversion.ui.json"
    )

    title: str = "Induced Polarization (IP) 2D Batch Inversion"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization pseudo 3d"

    data_object: PotentialElectrode
    chargeability_channel: FloatData
    chargeability_uncertainty: float | FloatData
    line_selection: LineSelectionOptions
    mesh: Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
    conductivity_model: float | FloatData
    lower_bound: float | FloatData | None = 0.0
    file_control: FileControlOptions = FileControlOptions()
    length_scale_y: None = None
    y_norm: None = None
