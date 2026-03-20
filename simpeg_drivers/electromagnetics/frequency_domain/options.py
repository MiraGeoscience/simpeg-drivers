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
from pydantic import field_validator

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

    @property
    def tx_offsets(self):
        """Return transmitter offsets from frequency metadata"""

        try:
            offset_data = self.data_object.metadata["EM Dataset"][
                "Frequency configurations"
            ]
            tx_offsets = {k["Frequency"]: k["Offset"] for k in offset_data}

        except KeyError as exception:
            msg = "Metadata must contain 'Frequency configurations' dictionary with 'Offset' data."
            raise GeoAppsError(msg) from exception

        return tx_offsets

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        return CONVERSION[self.data_object.unit]

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
    :param z_real_channel_bool: Vertical (real) component of impedance channel boolean.
    :param z_imag_channel_bool: Vertical (imaginary) component of impedance channel boolean.
    :param y_real_channel_bool: In-line (real) component of impedance channel boolean.
    :param y_imag_channel_bool: In-line (imaginary) component of impedance channel boolean.
    :param x_real_channel_bool: Cross-line (real) component of impedance channel boolean.
    :param x_imag_channel_bool: Cross-line (imaginary) component of impedance channel
    :param models: ConductivityModelOptions parameter.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_forward.ui.json"
    title: str = "Frequency-domain EM (FEM) Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: (
        MovingLoopGroundFEMReceivers
        | LargeLoopGroundFEMReceivers
        | AirborneFEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
    z_real_channel_bool: bool = False
    z_imag_channel_bool: bool = False
    y_real_channel_bool: bool = False
    y_imag_channel_bool: bool = False
    x_real_channel_bool: bool = False
    x_imag_channel_bool: bool = False
    models: ConductivityModelOptions


class FDEMInversionOptions(BaseFDEMOptions, BaseInversionOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param z_real_channel: Vertical (real) impedance channel.
    :param z_real_uncertainty: Vertical (real) impedance uncertainty channel.
    :param z_imag_channel: Vertical (imaginary) impedance channel.
    :param z_imag_uncertainty: Vertical (imaginary) impedance uncertainty channel.
    :param y_real_channel: In-line (real) impedance channel.
    :param y_real_uncertainty: In-line (real) impedance uncertainty channel.
    :param y_imag_channel: In-line (imaginary) impedance channel.
    :param y_imag_uncertainty: In-line (imaginary) impedance uncertainty channel
    :param x_real_channel: Cross-line (real) impedance channel.
    :param x_real_uncertainty: Cross-line (real) impedance uncertainty channel.
    :param x_imag_channel: Cross-line (imaginary) impedance channel.
    :param x_imag_uncertainty: Cross-line (imaginary) impedance uncertainty channel
    :param models: ConductivityModelOptions parameter.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_inversion.ui.json"
    title: str = "Frequency-domain EM (FEM) Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: (
        MovingLoopGroundFEMReceivers
        | LargeLoopGroundFEMReceivers
        | AirborneFEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
    z_real_channel: PropertyGroup | None = None
    z_real_uncertainty: PropertyGroup | None = None
    z_imag_channel: PropertyGroup | None = None
    z_imag_uncertainty: PropertyGroup | None = None
    y_real_channel: PropertyGroup | None = None
    y_real_uncertainty: PropertyGroup | None = None
    y_imag_channel: PropertyGroup | None = None
    y_imag_uncertainty: PropertyGroup | None = None
    x_real_channel: PropertyGroup | None = None
    x_real_uncertainty: PropertyGroup | None = None
    x_imag_channel: PropertyGroup | None = None
    x_imag_uncertainty: PropertyGroup | None = None

    models: ConductivityModelOptions

    directives: DirectiveOptions = DirectiveOptions()
