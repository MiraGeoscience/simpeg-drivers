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
    DrapeModelOptions,
    EMDataMixin,
)


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class TDEM1DForwardOptions(EMDataMixin, BaseForwardOptions):
    """
    Time Domain Electromagnetic forward options.

    :param z_channel_bool: Z-component data channel boolean.
    :param x_channel_bool: X-component data channel boolean.
    :param y_channel_bool: Y-component data channel boolean.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_forward.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Forward"
    inversion_type: str = "tdem 1d"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel_bool: bool
    x_channel_bool: None = None
    y_channel_bool: None = None
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"
    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]


class TDEM1DInversionOptions(EMDataMixin, BaseInversionOptions):
    """
    Time Domain Electromagnetic Inversion options.

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
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_inversion.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Inversion"
    inversion_type: str = "tdem 1d"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None
    x_channel: None = None
    x_uncertainty: None = None
    y_channel: None = None
    y_uncertainty: None = None
    length_scale_y: None = None
    y_norm: None = None
    data_units: str = "dB/dt (T/s)"
    model_type: str = "Conductivity (S/m)"
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

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Seconds (s)": 1.0,
            "Milliseconds (ms)": 1e-3,
            "Microseconds (us)": 1e-6,
        }
        return conversion[self.data_object.unit]
