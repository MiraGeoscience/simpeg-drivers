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
from geoh5py.objects import DrapeModel

from simpeg_drivers import assets_path
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    DrapeModelOptions,
    LineSelectionOptions,
)


class IP2DForwardOptions(BaseForwardOptions):
    """
    Induced Polarization 2D forward options.

    :param chargeability_channel_bool: Chargeability channel boolean.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters.
    :param line_selection: Line selection parameters.
    :param conductivity_model: Conductivity model.
    """

    name: ClassVar[str] = "Induced Polarization 2D Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_2d_forward.ui.json"
    )

    title: str = "Induced Polarization 2D Forward"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization 2d"

    chargeability_channel_bool: bool = True
    line_selection: LineSelectionOptions
    mesh: DrapeModel | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
    conductivity_model: float | FloatData


class IP2DInversionOptions(BaseInversionOptions):
    """
    Induced Polarization 2D inversion options.

    :param chargeability_channel: Chargeability data channel.
    :param chargeability_uncertainty: Chargeability data uncertainty channel.
    :param line_selection: Line selection parameters.
    :param drape_model: Drape model parameters.
    :param conductivity_model: Conductivity model.
    :param lower_bound: Lower bound for the inversion.
    :param length_scale_y: Inactive length scale in the y direction.
    :param y_norm: Inactive y normalization factor.
    """

    name: ClassVar[str] = "Induced Polarization 2D Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_2d_inversion.ui.json"
    )

    title: str = "Induced Polarization 2D Inversion"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization 2d"

    chargeability_channel: FloatData
    chargeability_uncertainty: float | FloatData | None = None
    line_selection: LineSelectionOptions
    mesh: DrapeModel | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()
    model_type: str = "Conductivity (S/m)"
    conductivity_model: float | FloatData
    lower_bound: float | FloatData | None = 0.0
    length_scale_y: None = None
    y_norm: None = None
