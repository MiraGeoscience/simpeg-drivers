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
from simpeg_drivers.electromagnetics.base_1d_options import Base1DOptions
from simpeg_drivers.electromagnetics.frequency_domain.options import (
    FDEMForwardOptions,
    FDEMInversionOptions,
)
from simpeg_drivers.options import DirectiveOptions


class FDEM1DForwardOptions(FDEMForwardOptions, Base1DOptions):
    """
    Frequency Domain Electromagnetic forward options.

    :param z_real_channel_bool: Z-component data channel boolean.
    :param z_imag_channel_bool: X-component data channel boolean.
    :param drape_model: Drape model options.
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_forward.ui.json"

    title: str = "Frequency-domain EM-1D (FEM-1D) Forward"
    inversion_type: str = "fdem 1d"

    z_real_channel_bool: bool
    z_imag_channel_bool: bool


class FDEM1DInversionOptions(FDEMInversionOptions, Base1DOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param z_real_channel: Real Z-component data channel.
    :param z_real_uncertainty: Real Z-component data channel uncertainty.
    :param z_imag_channel: Imaginary Z-component data channel.
    :param z_imag_uncertainty: Imaginary Z-component data channel uncertainty.
    :param drape_model: Drape model options.
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_inversion.ui.json"
    title: str = "Frequency-domain EM-1D (FEM-1D) Inversion"
    inversion_type: str = "fdem 1d"

    directives: DirectiveOptions = DirectiveOptions(
        sens_wts_threshold=100.0,
    )
    z_real_channel: PropertyGroup | None = None
    z_real_uncertainty: PropertyGroup | None = None
    z_imag_channel: PropertyGroup | None = None
    z_imag_uncertainty: PropertyGroup | None = None
