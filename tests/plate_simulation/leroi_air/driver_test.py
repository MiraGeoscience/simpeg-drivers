# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from geoh5py import Workspace

from simpeg_drivers.plate_simulation.leroi_air.driver import LeroiAirDriver

from . import generate_plate_options


# pylint: disable=protected-access


def test_leroi_air_driver_run_raises_on_subprocess_failure(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(workspace=geoh5)

    driver = LeroiAirDriver(opts)
    driver._interface = MagicMock()
    failed_result = MagicMock(
        spec=subprocess.CompletedProcess, returncode=1, stderr="err", stdout="out"
    )

    with patch(
        "simpeg_drivers.plate_simulation.leroi_air.driver.subprocess.run",
        return_value=failed_result,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            driver.run()

    assert "return code 1" in str(exc_info.value)
    assert "err" in str(exc_info.value)
    assert "out" in str(exc_info.value)
