# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                          '
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
from geoh5py.groups import SimPEGGroup
from pydantic import ValidationError

from simpeg_drivers.utils.tile_estimate import TileParameters


def test_simulation_validation_rejects_plate_simulation(tmp_path):
    simulation = MagicMock(spec=SimPEGGroup)
    simulation.options = {
        "run_command": "simpeg_drivers.plate_simulation.driver",
        "title": "Plate Simulation",
    }

    with Workspace.create(tmp_path / "test.geoh5") as geoh5:
        with pytest.raises(ValidationError, match="not a valid target"):
            TileParameters(geoh5=geoh5, simulation=simulation)
