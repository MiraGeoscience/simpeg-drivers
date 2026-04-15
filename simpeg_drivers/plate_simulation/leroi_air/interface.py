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

from pathlib import Path
from typing import Any

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import AirborneFEMReceivers, AirborneTEMReceivers
from numpy import array_split

from simpeg_drivers.plate_simulation.models.options import PlateOptions

from .options import LeroiAirOptions


class LeroiAirInterface:
    """Interface for running LeroiAir from geoh5py objects."""

    version: str = "8.0"

    def __init__(self, geoh5: Workspace, opts: LeroiAirOptions):
        self.geoh5 = geoh5
        self.opts = opts

    @property
    def aliased_values(self) -> dict[str, Any]:
        """Serves .cfl input file aliases and corresponding data to line formatter."""
        return {
            "TDFD": 1 if self.opts.domain == "time" else 2,
            "DO3D": 0 if self.opts.layered_earth_only else 1,
            "PRFL": 1,
            "ISTOP": 0,
            "ISW": 1,
            "NSX": len(self.opts.ontime_waveform),
            "STEP": 0 if self.opts.modelling.magnetic_field == "dBdt" else 1,
            "UNITS": 1,
            "NCHNL": len(self.opts.channels),
            "KRXW": 2,
            "REFTYM": self.opts.timing_mark,
            "OFFTIME": self.opts.offtime,
            "TXON": self.opts.ontime_waveform[:, 0],
            "TXAMP": self.opts.ontime_waveform[:, 1],
            "TOPN": self.opts.timing_mark + np.array([0.0] + self.opts.channels[:-1]),
            "TCLS": self.opts.timing_mark + np.array(self.opts.channels),
            "TMS": self.opts.timing_mark + np.array(self.opts.channels),
            "WIDTH": np.array([0.3, 0.3, 0.9]),
            "TXCLN": 0.0,
            "CMP": 3,
            "KPPM": 0,
            "NPPF": 3,
            "TXAREA": 1.0,
            "NTRN": 1,
            "ZRX0": 0.0,
            "XRX0": 0.0,
            "YRX0": 0.0,
            "NSTAT": len(self.opts.locations),
            "SURVEY": 2,
            "BAROMTRC": 1,
            "LINE_TAG": 0,
            "EAST": self.opts.locations[:, 0],
            "NORTH": self.opts.locations[:, 1],
            "ALT": 13 * np.ones(len(self.opts.locations)),
            "NLAYER": 2,
            "NPLATE": 1,
            "NLITH": 3,
            "GND_LVL": 0.0,
            "RES": self.opts.resistivities,
            "SIG_T": self.opts.conductivity_thicknesses,
            "RMU": np.ones_like(self.opts.resistivities),
            "REPS": np.ones_like(self.opts.resistivities),
            "CHRG": np.zeros_like(self.opts.resistivities),
            "CTAU": np.zeros_like(self.opts.resistivities),
            "CFREQ": np.ones_like(self.opts.resistivities),
            "LITH": np.array([1, 2]),
            "LITHP": 3,
            "THICK": self.opts.layer_thicknesses,
            "CELLW": self.opts.cell_size,
            "IPLATE": 1,
            "CNTR_East": self.opts.plate.reference[0],
            "CNTR_North": self.opts.plate.reference[1],
            "PLTOP": self.opts.plate.reference[2],
            "PLNGTH": self.opts.plate.strike_length,
            "DPWDTH": self.opts.plate.dip_length,
            "DZM": self.opts.plate.dip_direction,
            "DIP": self.opts.plate.dip,
        }

    def format_line(self, params: list[str]) -> str:
        """format a string from a list of params and the retrieved values."""
        values = [str(self.aliased_values[k]) for k in params]
        return f"{' '.join(values)} \t ! {', '.join(params)}"

    def format_line_from_array(self, param: str):
        values = [str(k) for k in self.aliased_values[param]]
        return f"{' '.join(values)} \t ! {param}"

    def format_multi_line(self, params: str | list[str]) -> str:
        """Format a multi-line string a column, or row oriented array."""
        if isinstance(params, str):
            values = array_split(self.aliased_values[param], 10)
        else:
            values = np.column_stack([self.aliased_values[k] for k in params])
        return self._format_multi_line(values) + "\t ! " + ", ".join(params)

    @property
    def record_2(self):
        return self.format_line(["TDFD", "DO3D", "PRFL", "ISTOP"])

    @property
    def record_3(self):
        return self.format_line(
            ["ISW", "NSX", "STEP", "UNITS", "NCHNL", "KRXW", "OFFTIME"]
        )

    @property
    def record_4(self):
        return self.format_multi_line(["TXON", "TXAMP"])

    @property
    def record_5(self):
        return self.format_line_from_array("TMS")
        # return self.format_multi_line(["TOPN", "TCLS"])

    @property
    def record_6(self):
        return self.format_line_from_array("WIDTH")

    @property
    def record_7(self):
        return self.format_line(["TXCLN", "CMP", "KPPM"])

    @property
    def record_7p1(self):
        return self.format_line(["NPPF"])

    @property
    def record_7p2(self):
        return self.format_line(["TXAREA", "NTRN"])

    @property
    def record_8(self):
        return self.format_line(["ZRX0", "XRX0", "YRX0"])

    @property
    def record_9(self):
        return self.format_line(["NSTAT", "SURVEY", "BAROMTRC", "LINE_TAG"])

    @property
    def record_9p1(self):
        return self.format_multi_line(["EAST", "NORTH", "ALT"])

    @property
    def record_10(self):
        return self.format_line(["NLAYER", "NPLATE", "NLITH", "GND_LVL"])

    @property
    def record_11(self):
        return self.format_multi_line(
            ["RES", "SIG_T", "RMU", "REPS", "CHRG", "CTAU", "CFREQ"]
        )

    @property
    def record_12(self):
        return self.format_multi_line(["LITH", "THICK"])

    @property
    def record_13(self):
        return self.format_line(["CELLW"])

    @property
    def record_14(self):
        return self.format_line(["LITHP", "CNTR_East", "CNTR_North", "PLTOP"])

    @property
    def record_15(self):
        return self.format_line(["PLNGTH", "DPWDTH", "DZM", "DIP"])

    def format_cfl_file(self):
        """
        Generates lines of text for an .cfl input file to run LeroiAir.

        Collects approriate 'Records' and adds lines to the input file one by one.
        """
        lines = []
        lines.append(self.opts.title)
        lines.append(self.record_2)
        lines.append(self.record_3)
        lines.append(self.record_4)
        lines.append(self.record_5)
        lines.append(self.record_6)
        lines.append(self.record_7)
        if self.aliased_values["KPPM"] > 0:
            lines.append(self.record_7p1)
        lines.append(self.record_7p2)
        lines.append(self.record_8)
        lines.append(self.record_9)
        lines.append(self.record_9p1)
        lines.append(self.record_10)
        lines.append(self.record_11)
        lines.append(self.record_12)
        lines.append(self.record_13)
        lines.append(self.record_14)
        lines.append(self.record_15)

        return "\n".join(lines) + "\n"

    def _format_multi_line(self, values: np.ndarray) -> str:
        """Format a multi-line string from array."""
        lines = []
        for row in values:
            lines.append(f"{' '.join([str(k) for k in row])}")
        return "\n".join(lines)

    def write_cfl_file(self, filepath: Path):
        with open(filepath, mode="w", encoding="utf-8") as f:
            return f.write(self.format_cfl_file())
