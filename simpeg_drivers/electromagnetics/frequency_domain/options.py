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

from functools import cached_property
from logging import getLogger
from pathlib import Path
from typing import ClassVar

from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.groups import PropertyGroup
from geoh5py.objects import (
    AirborneFEMReceivers,
    LargeLoopGroundFEMReceivers,
    MovingLoopGroundFEMReceivers,
)
from pydantic import AliasChoices, Field, field_validator

from simpeg_drivers import assets_path
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    ConductivityModelOptions,
    DirectiveOptions,
    EMDataMixin,
)


logger = getLogger(__name__)

CONVERSION = {
    "Hertz (Hz)": 1e-0,
    "KiloHertz (kHz)": 1e-3,
    "MegaHertz (MHz)": 1e-6,
    "Gigahertz (GHz)": 1e-9,
}


class BaseFDEMOptions(EMDataMixin):
    """
    Base Frequency Domain Electromagnetic options.
    """

    @cached_property
    def tx_offsets(self) -> list:
        """Return transmitter offsets from frequency metadata"""

        try:
            configs = self.data_object.metadata["EM Dataset"][
                "Frequency configurations"
            ]
            tx_offsets = [k["Offset"] for k in configs]

        except KeyError as exception:
            msg = "Metadata must contain 'Frequency configurations' dictionary with 'Offset' key."
            raise GeoAppsError(msg) from exception

        return tx_offsets

    @cached_property
    def coaxial(self) -> list:
        """Return transmitter offsets from frequency metadata"""

        try:
            configs = self.data_object.metadata["EM Dataset"][
                "Frequency configurations"
            ]
            coaxial = [k["Coaxial data"] for k in configs]

        except KeyError as exception:
            msg = "Metadata must contain 'Frequency configurations' dictionary with 'Coaxial data' key."
            raise GeoAppsError(msg) from exception

        return coaxial

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        return CONVERSION[getattr(self.data_object, "unit", "Hertz (Hz)")]

    @field_validator("inversion_type", mode="before")
    @classmethod
    def name_change(cls, value: str):
        if value == "fem":
            logger.warning(
                "Using 'fem' as inversion type is deprecated. Use 'fdem' instead."
            )
            return "fdem"
        return value


class FDEMForwardOptions(BaseForwardOptions, BaseFDEMOptions):
    """
    Frequency Domain Electromagnetic Forward options.

    :param receivers_orientation: Orientation of the receivers provided as a group.
    :param real_channel_bool: Real component of impedance channel boolean.
    :param imag_channel_bool: Imaginary component of impedance channel boolean.
    :param models: ConductivityModelOptions parameter.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_forward.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.frequency_domain.forward"
    title: str = "Frequency-domain EM (FEM) Forward"
    icon: str = "surveyairborneem"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: (
        MovingLoopGroundFEMReceivers
        | LargeLoopGroundFEMReceivers
        | AirborneFEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
    real_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices("z_real_channel_bool", "real_channel_bool"),
    )
    imag_channel_bool: bool = Field(
        False,
        validation_alias=AliasChoices("z_imag_channel_bool", "imag_channel_bool"),
    )
    models: ConductivityModelOptions


class FDEMInversionOptions(BaseFDEMOptions, BaseInversionOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param real_channel: Vertical (real) impedance channel.
    :param real_uncertainty: Vertical (real) impedance uncertainty channel.
    :param imag_channel: Vertical (imaginary) impedance channel.
    :param imag_uncertainty: Vertical (imaginary) impedance uncertainty channel.
    :param models: ConductivityModelOptions parameter.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_inversion.ui.json"
    run_command: str = "simpeg_drivers.electromagnetics.frequency_domain.inversion"
    title: str = "Frequency-domain EM (FEM) Inversion"
    icon: str = "surveyairborneem"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: (
        MovingLoopGroundFEMReceivers
        | LargeLoopGroundFEMReceivers
        | AirborneFEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
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
    directives: DirectiveOptions = DirectiveOptions()
