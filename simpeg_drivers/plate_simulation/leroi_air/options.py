# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.objects.surveys.electromagnetics.airborne_tem import AirborneTEMReceivers

from simpeg_drivers.plate_simulation.options import PlateSimulationOptions


@dataclass
class LeroiAirOptions:
    survey: AirborneTEMReceivers
    layer_resistivities: list[float]
    layer_thicknesses: list[float]
    plate_resistivities: list[float]
    plate_geometries: list[PlateModel]
    cell_size: float = 10.0
    magnetic_field: Literal["dBdt", "B"] = "dBdt"
    domain: Literal["time", "frequency"] = "time"
    layered_earth_only: bool = False

    @classmethod
    def from_plate_simulation_options(cls, options: PlateSimulationOptions) -> Self:
        simulation_options = options.simulation_parameters()
        return cls(
            survey=simulation_options.data_object,
            layer_resistivities=[
                options.model.overburden_options.overburden_property,
                options.model.background,
            ],
            layer_thicknesses=[options.model.overburden_options.thickness, 9999],
            plate_resistivities=[options.model.plate_options.plate_property],
            plate_geometries=[options.model.plate_options.geometry],
            magnetic_field="dBdt" if "dBdt" in simulation_options.data_units else "B",
        )

    @property
    def title(self) -> str:
        """Provides a generic title for all LeroiAir simulations."""
        return "LeroiAir modelling for plate-simulation package."

    @property
    def locations(self) -> np.ndarray:
        """Survey receiver locations."""
        return self.survey.vertices

    @property
    def n_stations(self) -> int:
        """Number of survey stations at which time channel data will be simulated"""
        return len(self.locations)

    @property
    def n_layers(self) -> int:
        """Number of background layers."""
        return len(self.layer_resistivities)

    @property
    def n_plates(self) -> int:
        """Number of plates."""
        return len(self.plate_geometries)

    @property
    def waveform(self) -> np.ndarray:
        """Survey transmitter waveform."""
        return self.survey.waveform

    @property
    def frequency(self) -> float:
        """
        Transmitter frequency.

        Can be set by the user in the metadata. If not set, it will be assumed
        that the waveform property contains a full halfcycle and the frequency
        will be calculated as the reciprocal of the provided waveform time span.
        """
        frequency = self.survey.metadata.get("frequency", None)
        if frequency is None:
            half_cycle_time = self.waveform[-1, 0] - self.waveform[0, 0]
            frequency = 1 / (2 * half_cycle_time)

        return frequency

    # TODO use units to convert time to milliseconds used by leroi.

    @property
    def channels(self) -> np.ndarray:
        """Time channel midpoints referenced from the timing_mark."""
        return self.survey.channels

    @property
    def channel_widths(self) -> np.ndarray:
        """Time channel widths."""
        channel_widths = self.survey.metadata.get("channel_widths", None)
        if channel_widths is None:
            channel_widths = np.diff([0] + self.channels)
        return channel_widths

    @property
    def timing_mark(self) -> float:
        """Reference point for timing of the channels."""
        return self.survey.timing_mark

    @property
    def units(self):
        """Units of the time channels."""
        return self.survey.unit

    @property
    def offtime(self) -> float:
        half_cycle = 1 / (2 * self.frequency)
        ontime = self.waveform[np.where(self.waveform[:, 1] == 0)[0][1], 0]
        return half_cycle - ontime

    @property
    def ontime_waveform(self) -> np.ndarray:
        """On-time waveform including leading and trailing 0 current times."""
        ontime_waveform = self.waveform[~self._offtime_mask(), :]
        endpoint = self.waveform[self._offtime_mask()][0, :]
        return np.vstack([ontime_waveform, endpoint])

    @property
    def resistivities(self) -> np.ndarray:
        """All resistivities."""
        return np.hstack([self.layer_resistivities, self.plate_resistivities])

    @property
    def conductivity_thicknesses(self) -> np.ndarray:
        """All conductivity thicknesses."""
        layer_sigma = self.layer_thicknesses * (1 / np.array(self.layer_resistivities))
        plate_sigma = [g.width for g in self.plate_geometries] * (
            1 / np.array(self.plate_resistivities)
        )
        return np.hstack([layer_sigma, plate_sigma])

    def _offtime_mask(self):
        """Returns a mask to slice the offtimes from the waveform array."""
        ind = [bool(np.isclose(k, 0)) for k in self.waveform[:, 1]]
        ind[0] = False
        return np.array(ind)
