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

import numpy as np
from dataclasses import dataclass
from typing import Literal, Self


from geoh5py.objects import Points
from geoapps_utils.modelling.plates import PlateModel

from simpeg_drivers.plate_simulation.options import PlateSimulationOptions


@dataclass
class LeroiAirOptions:
    survey: Points
    layer_resistivities: list[float]
    layer_thicknesses: list[float]
    plate_resistivities: list[float]
    plate_geometries: list[PlateModel]
    cell_size: float = 10.0
    magnetic_field: Literal["dBdt", "B"] = "dBdt"
    domain: Literal["time", "frequency"] = "time"
    layered_earth_only: bool = False

    @classmethod
    def from_plate_simulation_options(
        cls,
        options: PlateSimulationOptions
    ) -> Self:

        return cls(
            survey = options.simulations_parameters().survey,
            layer_resistivities = [
                options.model.overburden_options.overburden_property,
                options.background
            ],
            layer_thicknesses = [
                options.model.overburden_options.thickness,
                9999
            ],
            plate_resistivities = [options.model.plate.plate_property],
            plate_geometries = [options.model.plate.geometry],
            magnetic_field = "dBdt" if "dBdt" in options.data_units else "B"
        )

    @property
    def locations(self) -> np.ndarray:
        return self.survey.vertices

    @property
    def waveform(self) -> np.ndarray:
        return self.survey.waveform

    @property
    def channels(self) -> np.ndarray:
        return self.survey.channels

    @property
    def timing_mark(self) -> float:
        return self.survey.timing_mark

    @property
    def units(self):
        return self.survey.units

    @property
    def offtime(self) -> float:
        half_cycle = 1 / (2 * self.survey.metadata["frequency"])
        ontime = self.waveform[np.where(self.waveform[:, 1] == 0)[0][1], 0]
        return half_cycle - ontime

    @property
    def ontime_waveform(self) -> np.ndarray:
        """slice the waveform for the on times."""
        ontime_waveform = self.opts.waveform[~self._offtime_mask(), :]
        endpoint = self.opts.waveform[self._offtime_mask()][0, :]
        return np.vstack([ontime_waveform, endpoint])

    def _offtime_mask(self):
        """Returns a mask to slice the offtimes from the waveform array."""
        ind = [bool(np.isclose(k, 0)) for k in self.waveform[:, 1]]
        ind[0] = False
        return np.array(ind)