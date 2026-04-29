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

from functools import cached_property
from pathlib import Path
from typing import Any, Literal

import numpy as np
from geoh5py.shared.utils import fetch_active_workspace

from .options import LeroiAirOptions, SurveyOptions


class LeroiAirInterface:
    def __init__(self, opts: LeroiAirOptions):
        self.input = LeroiAirInput(opts)
        self.output = LeroiAirOutput(opts.survey)


class LeroiAirInput:
    """LeroiAir control file formatting from geoh5py objects and options."""

    version: str = "8.0"

    def __init__(self, opts: LeroiAirOptions):
        self.opts = opts

    @cached_property
    def aliased_values(self) -> dict[str, Any]:
        """Serves .cfl input file aliases and corresponding data to line formatter."""
        return {
            "TDFD": 1 if self.opts.domain == "time" else 2,
            "DO3D": 0 if self.opts.layered_earth_only else 1,
            "PRFL": 1,
            "ISTOP": 0,
            "ISW": 1,
            "NSX": len(self.opts.survey.ontime_waveform),
            "STEP": 0 if self.opts.magnetic_field == "dBdt" else 1,
            "UNITS": 1,
            "NCHNL": len(self.opts.survey.channels),
            "KRXW": 2,
            "REFTYM": self.opts.survey.timing_mark,
            "OFFTIME": self.opts.survey.offtime,
            "TXON": self.opts.survey.ontime_waveform[:, 0],
            "TXAMP": self.opts.survey.ontime_waveform[:, 1],
            "TMS": self.opts.survey.timing_mark + np.array(self.opts.survey.channels),
            "WIDTH": self.opts.survey.channel_widths,
            "TXCLN": 0.0,
            "CMP": 3,
            "KPPM": 0,
            "NPPF": 3,
            "TXAREA": 1.0,
            "NTRN": 1,
            "ZRX0": 0.0,
            "XRX0": 0.0,
            "YRX0": 0.0,
            "NSTAT": self.opts.survey.n_stations,
            "SURVEY": 2,
            "BAROMTRC": 1,
            "LINE_TAG": 0,
            "EAST": self.opts.survey.entity.locations[:, 0],
            "NORTH": self.opts.survey.entity.locations[:, 1],
            "ALT": self.opts.survey.drape_height(self.opts.topo),
            "NLAYER": self.opts.n_layers,
            "NPLATE": self.opts.n_plates,
            "NLITH": self.opts.n_layers + self.opts.n_plates,
            "GND_LVL": 0.0,
            "RES": self.opts.resistivities,
            "SIG_T": self.opts.conductivity_thicknesses,
            "RMU": np.ones_like(self.opts.resistivities),
            "REPS": np.ones_like(self.opts.resistivities),
            "CHRG": np.zeros_like(self.opts.resistivities),
            "CTAU": np.zeros_like(self.opts.resistivities),
            "CFREQ": np.ones_like(self.opts.resistivities),
            "LITH": 1 + np.arange(self.opts.n_layers, dtype=int),
            "LITHP": 1 + np.arange(self.opts.n_plates, dtype=int) + self.opts.n_layers,
            "THICK": self.opts.layer_thicknesses,
            "CELLW": self.opts.cell_size,
            "IPLATE": 1,
            "CNTR_East": [g.easting for g in self.opts.plate_geometries],
            "CNTR_North": [g.northing for g in self.opts.plate_geometries],
            "PLTOP": [-1 * g.elevation for g in self.opts.plate_geometries],
            "PLNGTH": [g.strike_length for g in self.opts.plate_geometries],
            "DPWDTH": [g.dip_length for g in self.opts.plate_geometries],
            "DZM": [g.direction for g in self.opts.plate_geometries],
            "DIP": [g.dip for g in self.opts.plate_geometries],
        }

    def _format_value(self, value: int | float) -> str:
        """
        Format a scalar value as an integer of bounded precision float.

        :param value: Value to format.
        """
        match value:
            case int() | np.integer():
                return str(int(value))
            case float() | np.floating():
                return self._format_float(value)
            case _:
                return str(value)

    def _format_float(self, value: float) -> str:
        """
        Format a float, truncating to float_precision only when needed.

        :param value: Value to format as a bounded precision float.
        """
        _, _, decimals = str(value).partition(".")
        if len(decimals) > self.opts.float_precision:
            return f"{value:.{self.opts.float_precision}f}"
        return str(value)

    def _format_scalar_params(self, params: list[str]) -> str:
        """
        Format one scalar value per param onto a single line.

        :param params: Parameter names to format a single line of scalar data.
        """
        values = [self._format_value(self.aliased_values[k]) for k in params]
        return f"{' '.join(values)} \t ! {', '.join(params)}"

    def _format_vector_param(self, param: str) -> str:
        """
        Format all elements of a single vector param onto a single line.

        :param param: Parameter name to format as a single line of vector data.
        """
        values = [self._format_value(v) for v in self.aliased_values[param]]
        return f"{' '.join(values)} \t ! {param}"

    def format_line(self, params: str | list[str]) -> str:
        """
        Format one or more param values on a single line.

        :param params: Parameter names to format as a single line.
        """
        if isinstance(params, str):
            return self._format_vector_param(params)
        return self._format_scalar_params(params)

    def format_multi_line(self, params: list[str]) -> str:
        """
        Format one or more vector param values as a row-per-entry table.

        :param params: Parameter names to format as a multi-line.
        """
        columns = [self.aliased_values[k] for k in params]
        rows = [
            " ".join(self._format_value(v) for v in row)
            for row in zip(*columns, strict=True)
        ]
        return "\n".join(rows) + "\t ! " + ", ".join(params)

    @property
    def record_2(self) -> str:
        return self.format_line(["TDFD", "DO3D", "PRFL", "ISTOP"])

    @property
    def record_3(self) -> str:
        return self.format_line(
            ["ISW", "NSX", "STEP", "UNITS", "NCHNL", "KRXW", "OFFTIME"]
        )

    @property
    def record_4(self) -> str:
        return self.format_multi_line(["TXON", "TXAMP"])

    @property
    def record_5(self) -> str:
        return self.format_line("TMS")

    @property
    def record_6(self) -> str:
        return self.format_line("WIDTH")

    @property
    def record_7(self) -> str:
        return self.format_line(["TXCLN", "CMP", "KPPM"])

    @property
    def record_7p1(self) -> str:
        return self.format_line(["NPPF"])

    @property
    def record_7p2(self) -> str:
        return self.format_line(["TXAREA", "NTRN"])

    @property
    def record_8(self) -> str:
        return self.format_line(["ZRX0", "XRX0", "YRX0"])

    @property
    def record_9(self) -> str:
        return self.format_line(["NSTAT", "SURVEY", "BAROMTRC", "LINE_TAG"])

    @property
    def record_9p1(self) -> str:
        return self.format_multi_line(["EAST", "NORTH", "ALT"])

    @property
    def record_10(self) -> str:
        return self.format_line(["NLAYER", "NPLATE", "NLITH", "GND_LVL"])

    @property
    def record_11(self) -> str:
        return self.format_multi_line(
            ["RES", "SIG_T", "RMU", "REPS", "CHRG", "CTAU", "CFREQ"]
        )

    @property
    def record_12(self) -> str:
        return self.format_multi_line(["LITH", "THICK"])

    @property
    def record_13(self) -> str:
        return self.format_line(["CELLW"])

    @property
    def record_14(self) -> str:
        return self.format_multi_line(["LITHP", "CNTR_East", "CNTR_North", "PLTOP"])

    @property
    def record_15(self) -> str:
        return self.format_multi_line(["PLNGTH", "DPWDTH", "DZM", "DIP"])

    def format_cfl_file(self) -> str:
        """
        Generates lines of text for an .cfl input file to run LeroiAir.

        Collects appropriate 'Records' and adds lines to the input file one by one.
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

    def write_cfl_file(self, filepath: Path) -> None:
        """
        Write the formatted .cfl input file to disk.

        :param filepath: Path where the .cfl file will be written.
        """
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(self.format_cfl_file())


class LeroiAirOutput:
    """LeroiAir output file parsing and saving to geoh5py objects/data."""

    _COMPONENT_ANCHORS: dict[str, str] = {
        "crossline": "TRANSVERSE COMPONENT",
        "inline": "IN-LINE COMPONENT",
        "vertical": "VERTICAL COMPONENT",
    }

    def __init__(self, opts: SurveyOptions):
        self.opts = opts

    def _find_data_start(self, chunk: list[str]) -> int:
        """
        Return the index of the first station data row within a section chunk.

        :param chunk: Chunk of data containing a header to index lines from.
        """
        header_idx = next(
            i
            for i, line in enumerate(chunk)
            if all(k in line for k in ["EAST", "NORTH", "ALT"])
        )
        return header_idx + 2

    def _slice_data_lines(self, lines: list[str], anchor: str) -> list[str]:
        """
        Slice the station data rows that follow the given section header.

        :param lines: Lines to slice.
        :param anchor: String marking the start of a chunk of output data.
        """
        anchor_idx = next(i for i, line in enumerate(lines) if anchor in line)
        chunk = lines[anchor_idx:]
        data_start = self._find_data_start(chunk)
        return chunk[data_start : data_start + self.opts.n_stations]

    def _extract_data(
        self, outfile: str | Path, component: Literal["inline", "crossline", "vertical"]
    ) -> np.ndarray:
        """
        Extract channel data for a single component from a LeroiAir .out file.

        :param outfile: Path to the output file from a LeroiAir run.
        :param component: Component to extract.
        """
        lines = Path(outfile).read_text(encoding="utf-8", errors="replace").splitlines()
        data_lines = self._slice_data_lines(lines, self._COMPONENT_ANCHORS[component])
        return np.array([line.split() for line in data_lines], dtype=float)[:, 4:]

    def save_to_geoh5(self, outfile: str | Path, out_group):
        """
        Save LeroiAir simulated data on the provided survey to geoh5.

        :param outfile: Path to output file from a LeroiAir run.
        :param out_group: Group where a copy of the survey will be saved
            along with all the data computed by LeroiAir.
        """

        survey = self.opts.entity.copy(parent=out_group, copy_children=False)
        for component in "inline", "crossline", "vertical":
            data = self._extract_data(outfile=outfile, component=component)
            entities = survey.add_data(
                {
                    f"fwd {component} [{i}]": {"values": data[:, i]}
                    for i in range(len(self.opts.channels))
                }
            )

            survey.create_property_group(name=component, properties=entities)
