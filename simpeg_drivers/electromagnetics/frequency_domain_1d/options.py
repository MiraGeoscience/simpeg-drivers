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

    :param vertical_real_channel_bool: Z-component data channel boolean.
    :param vertical_imag_channel_bool: Imaginary Z-component data channel boolean.
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
    vertical_real_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices(
            "z_real_channel_bool", "vertical_real_channel_bool"
        ),
    )
    vertical_imag_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices(
            "z_imag_channel_bool", "vertical_imag_channel_bool"
        ),
    )
    models: ConductivityModelOptions


class FDEM1DInversionOptions(BaseFDEMOptions, BaseInversionOptions, Base1DOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param vertical_real_channel: Real Z-component data channel.
    :param vertical_real_uncertainty: Real Z-component data channel uncertainty.
    :param vertical_imag_channel: Imaginary Z-component data channel.
    :param vertical_imag_uncertainty: Imaginary Z-component data channel uncertainty.
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
    vertical_real_channel: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_real_channel", "vertical_real_channel")
    )
    vertical_real_uncertainty: PropertyGroup | None = Field(
        None,
        validation_alias=AliasChoices(
            "z_real_uncertainty", "vertical_real_uncertainty"
        ),
    )
    vertical_imag_channel: PropertyGroup | None = Field(
        None, validation_alias=AliasChoices("z_imag_channel", "vertical_imag_channel")
    )
    vertical_imag_uncertainty: PropertyGroup | None = Field(
        None,
        validation_alias=AliasChoices(
            "z_imag_uncertainty", "vertical_imag_uncertainty"
        ),
    )
    models: ConductivityModelOptions
