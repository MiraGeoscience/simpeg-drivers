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
from typing import ClassVar, TypeAlias

from geoh5py.groups import PropertyGroup
from geoh5py.objects import (
    AirborneTEMReceivers,
    LargeLoopGroundTEMReceivers,
    MovingLoopGroundTEMReceivers,
)

from simpeg_drivers import assets_path
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    ConductivityModelOptions,
    EMDataMixin,
)


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class BaseTDEMOptions(EMDataMixin):
    """
    Base class for Time Domain Electromagnetic options.

    :param data_object: The data object containing the TDEM data.
    :param physical_property: The physical property being modeled (e.g., conductivity).
    :param data_units: The units of the TDEM data (e.g., "dB/dt (T/s)").
    """

    physical_property: str = "conductivity"
    data_units: str = "dB/dt (T/s)"
    inversion_type: str = "tdem"

    data_object: Receivers
    models: ConductivityModelOptions

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]


class TDEMForwardOptions(BaseTDEMOptions, BaseForwardOptions):
    """
    Time Domain Electromagnetic forward options.

    :param z_channel_bool: Z-component data channel boolean.
    :param x_channel_bool: X-component data channel boolean.
    :param y_channel_bool: Y-component data channel boolean.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_forward.ui.json"

    title: str = "Time-domain EM (TEM) Forward"

    z_channel_bool: bool | None = None
    x_channel_bool: bool | None = None
    y_channel_bool: bool | None = None


class TDEMInversionOptions(BaseTDEMOptions, BaseInversionOptions):
    """
    Time Domain Electromagnetic Inversion options.

    :param z_channel: Z-component data channel.
    :param z_uncertainty: Z-component data channel uncertainty.
    :param x_channel: X-component data channel.
    :param x_uncertainty: X-component data channel uncertainty.
    :param y_channel: Y-component data channel.
    :param y_uncertainty: Y-component data channel uncertainty.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_inversion.ui.json"
    title: str = "Time-domain EM (TEM) Inversion"

    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None
    x_channel: PropertyGroup | None = None
    x_uncertainty: PropertyGroup | None = None
    y_channel: PropertyGroup | None = None
    y_uncertainty: PropertyGroup | None = None
