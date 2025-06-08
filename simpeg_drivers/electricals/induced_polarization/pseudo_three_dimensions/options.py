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
    IPModelOptions,
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
    drape_model: DrapeModelOptions = DrapeModelOptions()
    file_control: FileControlOptions = FileControlOptions()
    models: IPModelOptions


class IPBatch2DInversionOptions(BaseInversionOptions):
    """
    Induced Polarization batch 2D inversion options.

    :param data_object: DC/IP survey object.
    :param chargeability_channel: Chargeability data channel.
    :param chargeability_uncertainty: Chargeability data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters common to all 2D simulations.
    :param file_control: File control parameters.
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
    file_control: FileControlOptions = FileControlOptions()
    models: IPModelOptions
