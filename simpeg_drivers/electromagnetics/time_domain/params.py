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
from simpeg_drivers.params import BaseForwardData, BaseInversionData, EMDataMixin


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class TimeDomainElectromagneticsForwardParams(EMDataMixin, BaseForwardData):
    """
    Parameter class for Time-domain Electromagnetic (TEM) -> conductivity forward simulation.

    :param z_channel_bool: Z-component data channel boolean.
    :param z_channel_uncertainty: Z-component data channel uncertainty.
    :param x_channel_bool: X-component data channel boolean.
    :param x_channel_uncertainty: X-component data channel uncertainty.
    :param y_channel_bool: Y-component data channel boolean.
    :param y_channel_uncertainty: Y-component data channel uncertainty.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    title: ClassVar[str] = "Time-domain EM (TEM) Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_forward.ui.json"

    inversion_type: str = "tdem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel_bool: bool | None = None
    x_channel_bool: bool | None = None
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]


class TimeDomainElectromagneticsInversionParams(EMDataMixin, BaseInversionData):
    """
    Parameter class for Time-domain Electromagnetic (TEM) -> conductivity inversion.

    :param z_channel: Z-component data channel.
    :param z_uncertainty: Z-component data channel uncertainty.
    :param x_channel: X-component data channel.
    :param x_uncertainty: X-component data channel uncertainty.
    :param y_channel: Y-component data channel.
    :param y_uncertainty: Y-component data channel uncertainty.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    title: ClassVar[str] = "Time-domain EM (TEM) Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem_inversion.ui.json"

    inversion_type: str = "tdem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None
    x_channel: PropertyGroup | None = None
    x_uncertainty: PropertyGroup | None = None
    y_channel: PropertyGroup | None = None
    y_uncertainty: PropertyGroup | None = None
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]
