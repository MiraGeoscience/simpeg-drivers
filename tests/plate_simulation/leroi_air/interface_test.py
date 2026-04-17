# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
import pytest
from geoh5py import Workspace

from simpeg_drivers.plate_simulation.leroi_air.interface import LeroiAirInterface

from . import generate_plate_options
from .conftest import FAKE_OUT, N_CHANNELS, N_STATIONS


def test_line_formatting(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(geoh5)

    interface = LeroiAirInterface(opts=opts)

    line = interface.format_line(["TXCLN", "CMP", "KPPM"])
    assert line == "0.0 3 0 \t ! TXCLN, CMP, KPPM"

    line = interface.format_line("TMS")
    assert line == "2.3 2.6 3.2 \t ! TMS"

    multi_line = interface.format_multi_line(["TMS", "WIDTH"])
    assert multi_line == "2.3 0.3\n2.6 0.3\n3.2 0.6\t ! TMS, WIDTH"


def test_format_cfl_file(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(geoh5)

    interface = LeroiAirInterface(opts=opts)
    cfl_str = interface.format_cfl_file()

    # title
    assert opts.title in cfl_str

    # record_2: TDFD, DO3D, PRFL, ISTOP
    assert "1 1 1 0 \t ! TDFD, DO3D, PRFL, ISTOP" in cfl_str

    # record_3: ISW, NSX, STEP, UNITS, NCHNL, KRXW, OFFTIME
    assert "1 8 0 1 3 2 1.6 \t ! ISW, NSX, STEP, UNITS, NCHNL, KRXW, OFFTIME" in cfl_str

    # record_4: TXON, TXAMP (multi-line waveform table)
    assert (
        "0.0 0.0\n"
        "0.5 0.3333\n"
        "1.0 0.6667\n"
        "1.5 1.0\n"
        "1.6 0.9\n"
        "1.7 0.6000\n"
        "1.8 0.3000\n"
        "1.9 0.0\t ! TXON, TXAMP"
    ) in cfl_str

    # record_5: TMS (time channel midpoints)
    assert "2.3 2.6 3.2 \t ! TMS" in cfl_str

    # record_6: WIDTH (time channel widths)
    assert "0.3 0.3 0.6 \t ! WIDTH" in cfl_str

    # record_7: TXCLN, CMP, KPPM
    assert "0.0 3 0 \t ! TXCLN, CMP, KPPM" in cfl_str

    # record_7p1 (NPPF) is only written when KPPM > 0; default KPPM=0 so absent
    assert "3 \t ! NPPF" not in cfl_str

    # record_7p2: TXAREA, NTRN
    assert "1.0 1 \t ! TXAREA, NTRN" in cfl_str

    # record_8: ZRX0, XRX0, YRX0
    assert "0.0 0.0 0.0 \t ! ZRX0, XRX0, YRX0" in cfl_str

    # record_9: NSTAT, SURVEY, BAROMTRC, LINE_TAG
    assert "6561 2 1 0 \t ! NSTAT, SURVEY, BAROMTRC, LINE_TAG" in cfl_str

    # record_9p1: EAST, NORTH, ALT — too long to assert explicitly

    # record_10: NLAYER, NPLATE, NLITH, GND_LVL
    assert "3 1 4 0.0 \t ! NLAYER, NPLATE, NLITH, GND_LVL" in cfl_str

    # record_11: RES, SIG_T, RMU, REPS, CHRG, CTAU, CFREQ (multi-line lithology table)
    assert (
        "1500.0 0.0333 1.0 1.0 0.0 0.0 1.0\n"
        "2000.0 0.5 1.0 1.0 0.0 0.0 1.0\n"
        "5000.0 0.4 1.0 1.0 0.0 0.0 1.0\n"
        "100.0 0.1 1.0 1.0 0.0 0.0 1.0\t ! RES, SIG_T, RMU, REPS, CHRG, CTAU, CFREQ"
    ) in cfl_str

    # record_12: LITH, THICK (multi-line layer table)
    assert ("1 50.0\n2 1000.0\n3 2000.0\t ! LITH, THICK") in cfl_str

    # record_13: CELLW
    assert "10.0 \t ! CELLW" in cfl_str

    # record_14: LITHP, CNTR_East, CNTR_North, PLTOP
    assert "4 0.0 0.0 0.0\t ! LITHP, CNTR_East, CNTR_North, PLTOP" in cfl_str

    # record_15: PLNGTH, DPWDTH, DZM, DIP
    assert "200.0 100.0 90.0 45.0\t ! PLNGTH, DPWDTH, DZM, DIP" in cfl_str


def test_slice_data_lines_returns_correct_station_rows(mock_interface):
    lines = FAKE_OUT.splitlines()
    anchor = LeroiAirInterface._COMPONENT_ANCHORS["x"]
    rows = mock_interface._slice_data_lines(lines, anchor)
    assert len(rows) == N_STATIONS
    assert rows[0].split()[4] == "1.1"
    assert rows[1].split()[4] == "4.4"


def test_extract_data_returns_channel_columns_only(mock_interface, fake_outfile):
    data = mock_interface._extract_data(fake_outfile, component="x")
    assert data.shape == (N_STATIONS, N_CHANNELS)


def test_extract_data_parses_transverse_component_values(mock_interface, fake_outfile):
    data = mock_interface._extract_data(fake_outfile, component="x")
    np.testing.assert_array_almost_equal(data[0], [1.1, 2.2, 3.3])
    np.testing.assert_array_almost_equal(data[1], [4.4, 5.5, 6.6])


def test_extract_data_parses_inline_component_values(mock_interface, fake_outfile):
    data = mock_interface._extract_data(fake_outfile, component="y")
    np.testing.assert_array_almost_equal(data[0], [7.7, 8.8, 9.9])
    np.testing.assert_array_almost_equal(data[1], [10.0, 11.1, 12.2])


def test_extract_data_parses_vertical_component_values(mock_interface, fake_outfile):
    data = mock_interface._extract_data(fake_outfile, component="z")
    np.testing.assert_array_almost_equal(data[0], [13.3, 14.4, 15.5])
    np.testing.assert_array_almost_equal(data[1], [16.6, 17.7, 18.8])


def test_format_value_int(mock_interface):
    assert mock_interface._format_value(3) == "3"
    assert mock_interface._format_value(np.int64(7)) == "7"


def test_format_value_float(mock_interface):
    assert mock_interface._format_value(1.5) == "1.5"
    assert mock_interface._format_value(1.123456789) == "1.1235"
    mock_interface.opts.float_precision = 2
    assert mock_interface._format_value(3.141592653) == "3.14"
