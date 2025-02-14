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
    AirborneFEMReceivers,
    LargeLoopGroundFEMReceivers,
    MovingLoopGroundFEMReceivers,
)

from simpeg_drivers import assets_path
from simpeg_drivers.params import BaseForwardOptions, BaseInversionOptions, EMDataMixin


Receivers: TypeAlias = (
    MovingLoopGroundFEMReceivers | LargeLoopGroundFEMReceivers | AirborneFEMReceivers
)


class FDEMForwardOptions(EMDataMixin, BaseForwardOptions):
    """
    Frequency Domain Electromagnetic Forward options.

    :param z_real_channel_bool: Real impedance channel boolean.
    :param z_imag_channel_bool: Imaginary impedance channel boolean.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Forward"
    title: ClassVar[str] = "Frequency-domain EM (FEM) Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fem_forward.ui.json"

    inversion_type: str = "fem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_real_channel_bool: bool
    z_imag_channel_bool: bool
    model_type: str = "Conductivity (S/m)"

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
            raise KeyError(msg) from exception

        return tx_offsets

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Hertz (Hz)": 1.0,
        }
        return conversion[self.data_object.unit]


class FDEMInversionOptions(EMDataMixin, BaseInversionOptions):
    """
    Frequency Domain Electromagnetic Inversion options.

    :param z_real_channel: Real impedance channel.
    :param z_real_uncertainty: Real impedance uncertainty channel.
    :param z_imag_channel: Imaginary impedance channel.
    :param z_imag_uncertainty: Imaginary impedance uncertainty channel.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    """

    name: ClassVar[str] = "Frequency Domain Electromagnetics Inversion"
    title: ClassVar[str] = "Frequency-domain EM (FEM) Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/fem_inversion.ui.json"

    inversion_type: str = "fem"
    physical_property: str = "conductivity"

    data_object: Receivers
    z_real_channel: PropertyGroup | None = None
    z_real_uncertainty: PropertyGroup | None = None
    z_imag_channel: PropertyGroup | None = None
    z_imag_uncertainty: PropertyGroup | None = None
    model_type: str = "Conductivity (S/m)"

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
            raise KeyError(msg) from exception

        return tx_offsets

    @property
    def unit_conversion(self):
        """Return time unit conversion factor."""
        conversion = {
            "Hertz (Hz)": 1.0,
        }
        return conversion[self.data_object.unit]
