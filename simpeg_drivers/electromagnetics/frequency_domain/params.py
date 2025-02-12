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
from simpeg_drivers.params import BaseForwardData, BaseInversionData, EMDataMixin


Receivers: TypeAlias = (
    MovingLoopGroundFEMReceivers | LargeLoopGroundFEMReceivers | AirborneFEMReceivers
)


class FrequencyDomainElectromagneticsForwardParams(EMDataMixin, BaseForwardData):
    """
    Parameter class for Frequency-domain Electromagnetic (FEM) simulation.

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

    # @property
    # def channels(self) -> list[str]:
    #     return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]
    #
    # def property_group_data(self, property_group: PropertyGroup):
    #     """
    #     Return dictionary of channel/data.
    #
    #     :param property_group: Property group uid
    #     """
    #     _ = property_group
    #     channels = self.data_object.channels
    #     return {k: None for k in channels}
    #
    # def data(self, component: str):
    #     """Returns array of data for chosen data component."""
    #     property_group = self.data_channel(component)
    #     return self.property_group_data(property_group)
    #
    # def uncertainty(self, component: str) -> float:
    #     """Returns uncertainty for chosen data component."""
    #     uid = self.uncertainty_channel(component)
    #     return self.property_group_data(uid)


class FrequencyDomainElectromagneticsInversionParams(EMDataMixin, BaseInversionData):
    """
    Parameter class for Frequency-domain Electromagnetic (FEM) -> conductivity inversion.

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

    # @property
    # def channels(self) -> list[str]:
    #     return ["_".join(k.split("_")[:2]) for k in self.__dict__ if "channel" in k]
    #
    # def property_group_data(self, property_group: PropertyGroup):
    #     """
    #     Return dictionary of channel/data.
    #
    #     :param property_group: Property group containing TEM data.
    #     """
    #     channels = self.data_object.channels
    #     group = self.data_object.fetch_property_group(name=property_group.name)
    #     properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
    #     data = {f: properties[i] for i, f in enumerate(channels)}
    #
    #     return data
    #
    # def data(self, component: str):
    #     """Returns array of data for chosen data component."""
    #     property_group = self.data_channel(component)
    #     return self.property_group_data(property_group)
    #
    # def uncertainty(self, component: str) -> float:
    #     """Returns uncertainty for chosen data component."""
    #     uid = self.uncertainty_channel(component)
    #     return self.property_group_data(uid)
