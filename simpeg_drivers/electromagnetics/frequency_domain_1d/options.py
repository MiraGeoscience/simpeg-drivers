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
from geoh5py.objects import AirborneFEMReceivers
from pydantic import AliasChoices, Field

from simpeg_drivers import assets_path
from simpeg_drivers.electromagnetics.base_1d_options import Base1DOptions
from simpeg_drivers.electromagnetics.frequency_domain.options import BaseFDEMOptions
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    ConductivityModelOptions,
    DirectiveOptions,
)


class FDEM1DForwardOptions(BaseForwardOptions, BaseFDEMOptions, Base1DOptions):
    """
    Frequency Domain Electromagnetic forward options.

    :param real_channel_bool: Real component data channel boolean.
    :param imag_channel_bool: Imaginary component data channel boolean.
    :param drape_model: Drape model options.
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_forward.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.frequency_domain_1d.forward"
    title: str = "Frequency-domain EM-1D (FEM-1D) Forward"
    icon: str = "surveyairborneem"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem 1d"
    data_object: AirborneFEMReceivers
    real_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices("z_real_channel_bool", "real_channel_bool"),
    )
    imag_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices("z_imag_channel_bool", "imag_channel_bool"),
    )
    models: ConductivityModelOptions


class FDEM1DInversionOptions(BaseFDEMOptions, BaseInversionOptions, Base1DOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param real_channel: Real component data channel.
    :param real_uncertainty: Real component data channel uncertainty.
    :param imag_channel: Imaginary component data channel.
    :param imag_uncertainty: Imaginary component data channel uncertainty.
    :param drape_model: Drape model options.
    """

    name: ClassVar[str] = "Frequency Domain 1D Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem1d_inversion.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.frequency_domain_1d.inversion"
    title: str = "Frequency-domain EM-1D (FEM-1D) Inversion"
    icon: str = "surveyairborneem"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem 1d"

    data_object: AirborneFEMReceivers
    directives: DirectiveOptions = DirectiveOptions(
        sens_wts_threshold=100.0,
    )
    real_channel: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_real_channel", "real_channel")
    )
    real_uncertainty: PropertyGroup | None = Field(
        None,
        validation_alias=AliasChoices("z_real_uncertainty", "real_uncertainty"),
    )
    imag_channel: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_imag_channel", "imag_channel")
    )
    imag_uncertainty: PropertyGroup | None = Field(
        None,
        validation_alias=AliasChoices("z_imag_uncertainty", "imag_uncertainty"),
    )
    models: ConductivityModelOptions
