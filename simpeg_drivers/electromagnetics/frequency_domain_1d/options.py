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

from geoh5py.groups import PropertyGroup

from simpeg_drivers import assets_path
from simpeg_drivers.electromagnetics.frequency_domain import (
    FDEMForwardOptions,
    FDEMInversionOptions,
)
from simpeg_drivers.options import DrapeModelOptions


class FDEM1DForwardOptions(FDEMForwardOptions):
    """
    Frequency Domain Electromagnetic forward options.

    :param z_channel_bool: Z-component data channel boolean.
    :param x_channel_bool: X-component data channel boolean.
    :param y_channel_bool: Y-component data channel boolean.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the FEM data
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_forward.ui.json"

    title: str = "Frequency-domain EM-1D (FEM-1D) Forward"
    inversion_type: str = "fdem 1d"
    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )


class FDEM1DInversionOptions(FDEMInversionOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param z_real_channel: Real Z-component data channel.
    :param z_real_uncertainty: Real Z-component data channel uncertainty.
    :param z_imag_channel: Imaginary Z-component data channel.
    :param z_imag_uncertainty: Imaginary Z-component data channel uncertainty.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the FEM data
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_inversion.ui.json"

    title: str = "Frequency-domain EM-1D (FEM-1D) Inversion"
    inversion_type: str = "fdem 1d"
    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )
    auto_scale_misfits: bool = False
    sens_wts_threshold: float = 100.0
    length_scale_y: None = None
    y_norm: None = None
