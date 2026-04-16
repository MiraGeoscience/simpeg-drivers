# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from unittest.mock import MagicMock

import pytest
from geoh5py import Workspace

from simpeg_drivers.plate_simulation.leroi_air.interface import LeroiAirInterface

from . import generate_plate_options


N_CHANNELS = 3
N_STATIONS = 2

FAKE_OUT = """\
          VERTICAL COMPONENT - nT/s

         TRANSMITTER POSITION      CHNL 1       CHNL 2       CHNL 3
         EAST     NORTH    ALT     2.300        2.600        3.200

  1      -100         0     13    13.3         14.4         15.5
  2       -87         0     13    16.6         17.7         18.8
-------------------------------------------------------------------------------------


          IN-LINE COMPONENT - nT/s

         TRANSMITTER POSITION      CHNL 1       CHNL 2       CHNL 3
         EAST     NORTH    ALT     2.300        2.600        3.200

  1      -100         0     13    7.7          8.8          9.9
  2       -87         0     13    10.0         11.1         12.2
-------------------------------------------------------------------------------------


          TRANSVERSE COMPONENT - nT/s

         TRANSMITTER POSITION      CHNL 1       CHNL 2       CHNL 3
         EAST     NORTH    ALT     2.300        2.600        3.200

  1      -100         0     13    1.1          2.2          3.3
  2       -87         0     13    4.4          5.5          6.6
-------------------------------------------------------------------------------------
"""


@pytest.fixture
def mock_interface():
    opts = MagicMock()
    opts.n_stations = N_STATIONS
    return LeroiAirInterface(opts=opts)


@pytest.fixture
def real_interface(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(geoh5)
    return LeroiAirInterface(opts=opts)


@pytest.fixture
def fake_outfile(tmp_path):
    path = tmp_path / "leroi.out"
    path.write_text(FAKE_OUT, encoding="utf-8")
    return path
