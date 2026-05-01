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
from geoh5py.groups import UIJsonGroup
from pydantic import BaseModel, ConfigDict, Field

from .options import LeroiAirOptions, SurveyOptions


class LeroiAirInterface:
    def __init__(self, opts: LeroiAirOptions):
        self.input = LeroiAirInput(opts)
        self.output = LeroiAirOutput(opts.survey)


class LeroiAirFields(BaseModel):
    """
    Self-documenting fields for the LeroiAir .cfl control file.

    Notes:
        - Aliases are LeroiAir's native .cfl parameter names; call
        ``model_dump(by_alias=True)`` to produce a record-ready dict.

        - The plate reference point (PRP) is the midpoint of the plate
        reference edge (PRE), which is the south edge of a pre-oriented
        north-south horizontal plate.  It serves as the origin for azimuth
        and dip orientations.

        - All elevations and altitudes are relative levels (RL), positive
        upward.  PLTOP is therefore negative for below-surface plates.

        - TXON and WAVEFORM describe the positive half-cycle only; LeroiAir
        constructs the full bipolar waveform by mirroring the second half as
        its negative.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    domain: Literal[1, 2] = Field(
        alias="TDFD", description="1 for time, 2 for frequency."
    )
    layered_earth_only: Literal[0, 1] = Field(
        alias="DO3D",
        default=1,
        description="1 to model plate and background and 0 to modelbackground only.",
    )
    profile: int = Field(
        alias="PRFL",
        default=1,
        description="Output formatted as columns of time channel data.",
    )
    model_validation: int = Field(
        alias="ISTOP",
        default=0,
        description="Prompt user with model description before running. ",
    )
    waveform_input_format: int = Field(
        alias="ISW",
        default=1,
        description="Specified that the waveform is read as a column of "
        "time in milliseconds (TXON) and current in amps "
        "(WAVEFORM)",
    )
    waveform_length: int = Field(
        alias="NSX",
        description="Number of samples in the waveform.  LeroiAir uses "
        "this field to parse the waveform in RECORD 4.",
    )
    waveform_times: np.ndarray = Field(
        alias="TXON", description="Time (in ms) sampling the waveform."
    )
    waveform_amplitude: np.ndarray = Field(
        alias="WAVEFORM", description="Amplitude (in amps) of the sampled waveform."
    )
    offtime: float = Field(
        alias="OFFTIME",
        description="Time (in ms) between the end of the ontime pulse of the "
        "first half-cycle and the negative ontime pulse of the "
        "second half-cycle.",
    )
    magnetic_field: Literal[0, 1] = Field(
        alias="STEP",
        description="LeroiAir will simulate dBdt data if 0 and B data if 1.",
    )
    magnetic_field_units: Literal[1, 2, 3] = Field(
        alias="UNITS",
        default=1,
        description="Units of the exported data. If dBdt data is requested, "
        "then 1: nT/s, 2: pT/s, 3, fT/s.  If B data is requested, "
        "then 1: nT, 2: pT, 3, fT.",
    )
    number_of_time_channels: int = Field(
        alias="NCHNL",
        description="Number of time channels to simulate. LeroiAir uses this "
        "field to parse the time channel data in RECORD 5.",
    )
    time_channel_format: int = Field(
        alias="KRXW",
        default=2,
        description="Specifies that the time channels are provided in RECORDS "
        "5 and 6 as time gate centers (TMS) and widths (WIDTH) in "
        "milliseconds.",
    )
    time_channel_centers: np.ndarray = Field(
        alias="TMS", description="Time gate centers in milliseconds."
    )
    time_channel_widths: np.ndarray = Field(
        alias="WIDTH", description="Time gate widths in milliseconds."
    )
    component: int = Field(
        alias="CMP",
        default=3,
        description="Exports all 3 components (vertical, inline, crossline).",
    )
    normalization: int = Field(
        alias="KPPM",
        default=0,
        description="No normalization applied to simulated data.",
    )
    transmitter_angle: float = Field(
        alias="TXCLN",
        default=0.0,
        description="Transmitter dipole axis angle in degrees measured from "
        "the vertical.",
    )
    transmitter_area: float = Field(
        alias="TXAREA", default=1.0, description="Assumes a unit transmitter area."
    )
    transmitter_turns: int = Field(
        alias="NTRN",
        default=1,
        description="Assumes a single turn of the transmitter wire.",
    )
    receiver_vertical_offset: float = Field(
        alias="ZRX0", description="Vertical Tx_Rx offset. Assumed coincident"
    )
    receiver_inline_offset: float = Field(
        alias="XRX0", description="In-line horizontal Tx-Rx offset. Assumed coincident."
    )
    receiver_transverse_offset: float = Field(
        alias="YRX0",
        description="Transverse horizontal Tx-Rx offset. Assumed coincident.",
    )
    number_of_stations: int = Field(
        alias="NSTAT", description="Total number of receiver sites."
    )
    survey_data_type: int = Field(
        alias="SURVEY",
        default=2,
        description="Variable altitude and course with constant Tx-Rx.",
    )
    altitude_format: int = Field(
        alias="BAROMTRC",
        default=1,
        description="Altitudes are in metres above sea level.",
    )
    line_tagging: int = Field(
        alias="LINE_TAG",
        default=0,
        description="All stations tagged with default (1000).",
    )
    station_easting: np.ndarray = Field(
        alias="EAST", description="Transmitter easting (m)."
    )
    station_northing: np.ndarray = Field(
        alias="NORTH", description="Transmitter northing (m)."
    )
    station_altitude: np.ndarray = Field(
        alias="ALT", description="Transmitter altitude (m above sea level)."
    )
    number_of_layers: int = Field(
        alias="NLAYER", description="Number of layers including the basement.", gt=0
    )
    number_of_plates: int = Field(
        alias="NPLATE", description="Number of thin plates in the basement.", lt=9
    )
    number_of_lithologies: int = Field(
        alias="NLITH",
        description="Total number of layer plus plate lithologies.",
        gt=0,
    )
    ground_level: float = Field(
        alias="GND_LVL",
        default=0.0,
        description="Relative level of flat surface fixed at zero metres.",
    )
    resistivity: np.ndarray = Field(
        alias="RES", description="Resistivity of each lithology (ohm-m)."
    )
    conductance: np.ndarray = Field(
        alias="SIG_T",
        description="Conductance (conductivity-thickness product) of each lithology.",
    )
    magnetic_permeability: np.ndarray = Field(
        alias="RMU", description="Relative magnetic permeability. No contrast assumed."
    )
    dielectric_permittivity: np.ndarray = Field(
        alias="REPS",
        description="Relative dielectric permittivity. No contrast assumed.",
    )
    chargeability: np.ndarray = Field(
        alias="CHRG", description="Cole-Cole chargeability. No IP assumed."
    )
    cole_cole_time_constant: np.ndarray = Field(
        alias="CTAU", description="Cole-Cole time constant. No IP assumed."
    )
    cole_cole_frequency_constant: np.ndarray = Field(
        alias="CFREQ", description="Cole-Cole frequency constant. No IP assumed."
    )
    layer_lithology: np.ndarray = Field(
        alias="LITH", description="Integer lithology index assigned to each layer."
    )
    layer_thickness: np.ndarray = Field(
        alias="THICK", description="Thickness of each overburden layer (m)."
    )
    plate_lithology: np.ndarray = Field(
        alias="LITHP", description="Integer lithology index assigned to each plate."
    )
    cell_width: float = Field(
        alias="CELLW", description="Cell dimension for plate discretization (m)."
    )
    plate_reference_point_easting: np.ndarray = Field(
        alias="CNTR_East", description="Easting of the PRP (m)."
    )
    plate_reference_point_northing: np.ndarray = Field(
        alias="CNTR_North", description="Northing of the PRP (m)."
    )
    plate_altitude: np.ndarray = Field(
        alias="PLTOP",
        description="Altitude relative to the ground (GND_LVL) in meter,"
        "negative downward.",
    )
    plate_strike_length: np.ndarray = Field(
        alias="PLNGTH", description="Strike length of each plate (m)."
    )
    plate_dip_length: np.ndarray = Field(
        alias="DPWDTH", description="Dip length of each plate (m)."
    )
    plate_dip_azimuth: np.ndarray = Field(
        alias="DZM",
        description="Dip azimuth of each plate in degrees east of north "
        "(0 ≤ DZM ≤ 180).",
    )
    plate_dip: np.ndarray = Field(
        alias="DIP", description="Dip angle of each plate in degrees (0 ≤ DIP < 180)."
    )


class LeroiAirInput:
    """LeroiAir control file formatting from geoh5py objects and options."""

    version: str = "8.0"

    def __init__(self, opts: LeroiAirOptions):
        self.opts = opts

    @cached_property
    def aliased_values(self) -> dict[str, Any]:
        """Serves .cfl input file aliases and corresponding data to line formatter."""
        return LeroiAirFields(
            domain=1 if self.opts.domain == "time" else 2,
            magnetic_field=int(self.opts.step),
            layered_earth_only=0 if self.opts.layered_earth_only else 1,
            waveform_length=len(self.opts.survey.ontime_waveform),
            waveform_times=self.opts.survey.ontime_waveform[:, 0],
            waveform_amplitude=self.opts.survey.ontime_waveform[:, 1],
            offtime=self.opts.survey.offtime,
            output_quantity=int(self.opts.step),
            number_of_time_channels=len(self.opts.survey.channels),
            time_channel_centers=(
                self.opts.survey.timing_mark + np.array(self.opts.survey.channels)
            ),
            time_channel_widths=self.opts.survey.channel_widths,
            number_of_stations=self.opts.survey.n_stations,
            station_easting=self.opts.survey.entity.locations[:, 0],
            station_northing=self.opts.survey.entity.locations[:, 1],
            station_altitude=self.opts.survey.drape_height(self.opts.topo),
            receiver_vertical_offset=self.opts.survey.entity.vertical_offset or 0.0,
            receiver_inline_offset=self.opts.survey.entity.inline_offset or 0.0,
            receiver_transverse_offset=self.opts.survey.entity.crossline_offset or 0.0,
            number_of_layers=self.opts.n_layers,
            number_of_plates=self.opts.n_plates,
            number_of_lithologies=self.opts.n_layers + self.opts.n_plates,
            resistivity=self.opts.resistivities,
            conductance=self.opts.conductivity_thicknesses,
            magnetic_permeability=np.ones_like(self.opts.resistivities),
            dielectric_permittivity=np.ones_like(self.opts.resistivities),
            chargeability=np.zeros_like(self.opts.resistivities),
            cole_cole_time_constant=np.zeros_like(self.opts.resistivities),
            cole_cole_frequency_constant=np.ones_like(self.opts.resistivities),
            layer_lithology=1 + np.arange(self.opts.n_layers, dtype=int),
            plate_lithology=(
                1 + np.arange(self.opts.n_plates, dtype=int) + self.opts.n_layers
            ),
            layer_thickness=np.array(self.opts.layer_thicknesses),
            cell_width=self.opts.cell_size,
            plate_reference_point_easting=np.array(
                [g.easting for g in self.opts.plate_geometries]
            ),
            plate_reference_point_northing=np.array(
                [g.northing for g in self.opts.plate_geometries]
            ),
            plate_altitude=np.array(
                [-1 * g.elevation for g in self.opts.plate_geometries]
            ),
            plate_strike_length=np.array(
                [g.strike_length for g in self.opts.plate_geometries]
            ),
            plate_dip_length=np.array(
                [g.dip_length for g in self.opts.plate_geometries]
            ),
            plate_dip_azimuth=np.array(
                [g.direction for g in self.opts.plate_geometries]
            ),
            plate_dip=np.array([g.dip for g in self.opts.plate_geometries]),
        ).model_dump(by_alias=True)

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
        return self.format_multi_line(["TXON", "WAVEFORM"])

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

    def save_to_geoh5(
        self, outfile: str | Path, out_group: UIJsonGroup, normalization: float = 1
    ):
        """
        Save LeroiAir simulated data on the provided survey to geoh5.

        :param outfile: Path to output file from a LeroiAir run.
        :param out_group: Group where a copy of the survey will be saved
            along with all the data computed by LeroiAir.
        :param normalization: Normalization multiplied against the data
            before saving.
        """

        survey = self.opts.entity.copy(parent=out_group, copy_children=False)
        for component in "inline", "crossline", "vertical":
            data = self._extract_data(outfile=outfile, component=component)
            entities = survey.add_data(
                {
                    f"fwd {component} [{i}]": {"values": data[:, i] * normalization}
                    for i in range(len(self.opts.channels))
                }
            )

            survey.create_property_group(name=component, properties=entities)
