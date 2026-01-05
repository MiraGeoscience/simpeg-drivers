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
from geoh5py.objects import Points

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver import (
    lower_percent_mask,
    lower_percentile_mask,
    sensitivity_mask,
)


def test_lower_percentile_mask():
    sensitivity = np.arange(200.0)
    sensitivity[sensitivity > 100] = np.nan
    cutoff = 10
    mask = lower_percentile_mask(sensitivity, cutoff)
    assert np.sum(mask) == 90


def test_lower_percent_mask():
    sensitivity = np.arange(200.0)
    sensitivity[sensitivity > 100] = np.nan
    cutoff = 10
    mask = lower_percent_mask(sensitivity, cutoff)
    assert np.all(sensitivity[mask] > 10)


def test_lower_log_percent_mask():
    sensitivity = np.hstack([[0], np.logspace(-5, -1, 5), np.logspace(1, 7, 7)])
    sensitivity[sensitivity > 1e5] = np.nan
    cutoff = 10
    mask = lower_percent_mask(sensitivity, cutoff, logspace=True)
    assert np.all(sensitivity[mask] > 1e-4)


def test_sensitivity_mask(tmp_path):
    with Workspace.create(tmp_path / f"{__name__}.geoh5") as ws:
        pts = Points.create(ws, name="test", vertices=np.random.randn(100, 3))
        data = pts.add_data({"sensitivity": {"values": np.abs(np.random.randn(100))}})

        assert np.all(
            sensitivity_mask(sensitivity=data, cutoff=10, method="percentile")
            == lower_percentile_mask(data.values, 10)
        )
        assert np.all(
            sensitivity_mask(sensitivity=data, cutoff=10, method="percent")
            == lower_percent_mask(data.values, 10)
        )
        assert np.all(
            sensitivity_mask(sensitivity=data, cutoff=10, method="log_percent")
            == lower_percent_mask(data.values, 10, logspace=True)
        )
        with pytest.raises(ValueError, match=r"Invalid method\. Must be 'percentile'"):
            sensitivity_mask(sensitivity=data, cutoff=10, method="invalid_method")
