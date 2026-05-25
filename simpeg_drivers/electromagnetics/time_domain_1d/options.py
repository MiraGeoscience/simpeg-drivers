# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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
from pydantic import AliasChoices, Field

from simpeg_drivers import assets_path
from simpeg_drivers.electromagnetics.base_1d_options import Base1DOptions
from simpeg_drivers.electromagnetics.time_domain.options import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)
from simpeg_drivers.options import (
    DirectiveOptions,
)


class TDEM1DForwardOptions(TDEMForwardOptions, Base1DOptions):
    """
    Time Domain Electromagnetic forward options.

    :param vertical_channel_bool: Z-component data channel boolean.
    :param drape_model: Options for drape mesh.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_forward.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.time_domain_1d.forward"
    title: str = "Time-domain EM-1D (TEM-1D) Forward"
    icon: str = "surveyairborneem"
    inversion_type: str = "tdem 1d"

    vertical_channel_bool: bool = Field(
        True, validation_alias=AliasChoices("z_channel_bool", "vertical_channel_bool")
    )


class TDEM1DInversionOptions(TDEMInversionOptions, Base1DOptions):
    """
    Time Domain Electromagnetic Inversion options.

    :param vertical_channel: Z-component data channel.
    :param vertical_uncertainty: Z-component data channel uncertainty.
    :param drape_model: Options for drape mesh.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_inversion.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.time_domain_1d.inversion"
    title: str = "Time-domain EM-1D (TEM-1D) Inversion"
    icon: str = "surveyairborneem"
    inversion_type: str = "tdem 1d"

    vertical_channel: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_channel", "vertical_channel")
    )
    vertical_uncertainty: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_uncertainty", "vertical_uncertainty")
    )

    directives: DirectiveOptions = DirectiveOptions(
        sens_wts_threshold=100.0,
    )
