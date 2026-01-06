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

from logging import getLogger
from pathlib import Path
from typing import ClassVar, TypeAlias

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
    EMDataMixin,
)


Receivers: TypeAlias = (
    MovingLoopGroundFEMReceivers | LargeLoopGroundFEMReceivers | AirborneFEMReceivers
)

logger = getLogger(__name__)


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
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]

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

    :param z_real_channel_bool: Real impedance channel boolean.
    :param z_imag_channel_bool: Imaginary impedance channel boolean.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_forward.ui.json"
    title: str = "Frequency-domain EM (FEM) Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: Receivers
    z_real_channel_bool: bool
    z_imag_channel_bool: bool
    models: ConductivityModelOptions


class FDEMInversionOptions(BaseFDEMOptions, BaseInversionOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param z_real_channel: Real impedance channel.
    :param z_real_uncertainty: Real impedance uncertainty channel.
    :param z_imag_channel: Imaginary impedance channel.
    :param z_imag_uncertainty: Imaginary impedance uncertainty channel.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fdem_inversion.ui.json"
    title: str = "Frequency-domain EM (FEM) Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "fdem"

    data_object: Receivers
    z_real_channel: PropertyGroup | None = None
    z_real_uncertainty: PropertyGroup | None = None
    z_imag_channel: PropertyGroup | None = None
    z_imag_uncertainty: PropertyGroup | None = None
    models: ConductivityModelOptions
