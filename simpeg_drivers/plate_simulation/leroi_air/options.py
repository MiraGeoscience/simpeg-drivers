# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from typing import Literal, Self

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups import SimPEGGroup
from geoh5py.objects.surveys.electromagnetics.airborne_tem import AirborneTEMReceivers
from pydantic import BaseModel, ConfigDict, model_validator
from scipy.interpolate import LinearNDInterpolator

from simpeg_drivers.components.topography import InversionTopography
from simpeg_drivers.electromagnetics.time_domain.options import TDEMForwardOptions
from simpeg_drivers.plate_simulation.options import ModelOptions


TIME_UNIT_CONVERSION = {
    "Seconds (s)": 1e3,
    "Milliseconds (ms)": 1,
    "Microseconds (us)": 1e-3,
    "Nanoseconds (ns)": 1e-6,
}


class SurveyOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    entity: AirborneTEMReceivers

    @property
    def waveform(self) -> np.ndarray:
        """Waveform in expected units of milliseconds."""
        waveform = self.entity.waveform.copy()
        waveform[:, 0] *= TIME_UNIT_CONVERSION[self.entity.unit]
        return waveform

    @property
    def timing_mark(self) -> float:
        """Timing mark in expected units of milliseconds."""
        timing_mark = self.entity.timing_mark
        timing_mark *= TIME_UNIT_CONVERSION[self.entity.unit]
        return timing_mark

    @property
    def channels(self) -> np.ndarray:
        """Channels in expected units of milliseconds."""
        channels = self.entity.channels.copy()
        channels *= TIME_UNIT_CONVERSION[self.entity.unit]
        return channels

    @property
    def frequency(self) -> float:
        """
        Transmitter frequency.

        Can be set by the user in the metadata. If not set, it will be assumed
        that the waveform property contains a full halfcycle and the frequency
        will be calculated as the reciprocal of the provided waveform time span.
        """
        frequency = self.entity.metadata.get("frequency", None)
        if frequency is None:
            half_cycle_seconds = (self.waveform[-1, 0] - self.waveform[0, 0]) / 1e3
            frequency = 1 / (2 * half_cycle_seconds)

        return frequency

    @property
    def channel_widths(self) -> np.ndarray:
        """Time channel widths."""
        channel_widths = self.entity.metadata.get("channel_widths", None)
        if channel_widths is None:
            channel_widths = np.diff(np.r_[0, self.channels])
        else:
            channel_widths *= TIME_UNIT_CONVERSION[self.entity.unit]
        return channel_widths

    @property
    def _ontime(self) -> float:
        """Time at which the transmitter current turns off."""
        return float(self.waveform[self._offtime_mask(), 0][0])

    @property
    def offtime(self) -> float:
        """
        Time at which the transmitter current is zero.

        This offtime is based on system frequency and may include times that
        are not accounted for by the waveform.
        """
        half_cycle = 1000 / (2 * self.frequency)
        zero_current_ind = np.where(self.waveform[:, 1] == 0)[0]
        first_zero = 1 if self.waveform[0, 1] == 0.0 else 0
        ontime = self.waveform[zero_current_ind][first_zero, 0]

        return half_cycle - ontime

    @property
    def ontime_waveform(self) -> np.ndarray:
        """On-time waveform including leading and trailing 0 current times."""
        ontime_waveform = self.waveform[~self._offtime_mask(), :]
        endpoint = self.waveform[self._offtime_mask()][0, :]
        return np.vstack([ontime_waveform, endpoint])

    @property
    def n_stations(self) -> int:
        """Number of survey stations at which time channel data will be simulated."""
        return len(self.entity.locations)

    def drape_height(self, topo: np.ndarray) -> np.ndarray:
        """
        Survey height over topography.

        :param topo: Topography array of x, y, elevation.

        :returns Array of survey height over topography.
        """

        survey_locs = self.entity.locations.copy()
        topo_interp = LinearNDInterpolator(topo[:, :2], topo[:, 2])
        topo_at_survey_locations = topo_interp(survey_locs[:, 0], survey_locs[:, 1])

        return survey_locs[:, 2] - topo_at_survey_locations

    def _offtime_mask(self) -> np.ndarray:
        """Mask selecting off-time rows from the waveform array."""
        mask = np.isclose(self.waveform[:, 1], 0)
        mask[0] = False
        return mask


class LeroiAirOptions(BaseModel):
    """Configuration for a LeroiAir airborne TEM forward simulation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = "LeroiAir modelling for plate-simulation package."
    out_group: SimPEGGroup
    survey: SurveyOptions
    topo: np.ndarray
    layer_resistivities: list[float]
    layer_thicknesses: list[float]
    plate_resistivities: list[float]
    plate_geometries: list[PlateModel]
    cell_size: float = 10.0
    step: bool = True
    domain: Literal["time", "frequency"] = "time"
    layered_earth_only: bool = False
    float_precision: int = 4

    @model_validator(mode="after")
    def validate_layer_lengths_match(self) -> Self:
        """Ensure layer resistivities and thicknesses have equal length."""
        if len(self.layer_resistivities) != len(self.layer_thicknesses):
            raise ValueError(
                "layer_resistivities and layer_thicknesses must have the same length."
            )
        return self

    @model_validator(mode="after")
    def validate_plate_lengths_match(self) -> Self:
        """Ensure plate resistivities and geometries have equal length."""
        if len(self.plate_resistivities) != len(self.plate_geometries):
            raise ValueError(
                "plate_resistivities and plate_geometries must have the same length."
            )
        return self

    @classmethod
    def from_plate_simulation_options(
        cls, model: ModelOptions, simulation: TDEMForwardOptions
    ) -> Self:
        """Construct from a :class:`PlateSimulationOptions` instance."""

        survey = simulation.data_object

        if simulation.active_cells.topography_object is None:
            raise NotImplementedError(
                "Passing active cells directly does not currently work for simulating "
                "plates using the LeroiAir option.  Simulation options must contain a "
                "topography object."
            )

        topo_xyz = InversionTopography(survey.workspace, simulation).locations

        return cls(
            survey=SurveyOptions(entity=survey),
            topo=topo_xyz,
            layer_resistivities=[
                model.overburden_options.overburden_property,
                model.background,
            ],
            layer_thicknesses=[model.overburden_options.thickness, 9999],
            plate_resistivities=[model.plate_options.plate_property],
            plate_geometries=[model.plate_options.geometry],
            step="dBdt" in simulation.get("data_units", "dBdt"),
            out_group=simulation.out_group,
        )

    @property
    def n_layers(self) -> int:
        """Number of background layers."""
        return len(self.layer_resistivities)

    @property
    def n_plates(self) -> int:
        """Number of plates."""
        return len(self.plate_geometries)

    @property
    def resistivities(self) -> np.ndarray:
        """All resistivities."""
        return np.hstack([self.layer_resistivities, self.plate_resistivities])

    @property
    def conductivity_thicknesses(self) -> np.ndarray:
        """All conductivity thicknesses."""
        sigma = []
        layer_conductivities = 1 / np.array(self.layer_resistivities)
        sigma.append(self.layer_thicknesses * layer_conductivities)
        plate_conductivities = 1 / np.array(self.plate_resistivities)
        sigma.append([g.width for g in self.plate_geometries] * plate_conductivities)

        return np.hstack(sigma)
