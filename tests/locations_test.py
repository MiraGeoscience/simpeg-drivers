# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from geoh5py.objects import Grid2D, Points

from simpeg_drivers.components.locations import InversionLocations
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import MVIInversionOptions
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def get_mvi_params(tmp_path: Path) -> MVIInversionOptions:
    geoh5, enitiy, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=(2,),
        n_electrodes=2,
        n_lines=2,
        inversion_type="magnetic_vector",
    )
    with geoh5.open():
        tmi_channel = survey.add_data(
            {"tmi": {"values": np.random.rand(survey.n_vertices)}}
        )
    params = MVIInversionOptions(
        geoh5=geoh5,
        data_object=survey,
        tmi_channel=tmi_channel,
        tmi_uncertainty=1.0,
        active_cells=ActiveCellsOptions(topography_object=topography),
        mesh=model.parent,
        starting_model=model,
    )
    return params


def test_mask(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    with geoh5.open():
        locations = InversionLocations(geoh5, params)
        loc_mask = [0, 1, 1, 0]
        locations.mask = loc_mask
        assert isinstance(locations.mask, np.ndarray)
        assert locations.mask.dtype == bool
        loc_mask = [0, 1, 2, 3]
        with pytest.raises(ValueError) as excinfo:
            locations.mask = loc_mask
        assert "Badly formed" in str(excinfo.value)


def test_get_locations(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    with geoh5.open():
        locs = np.ones((10, 3), dtype=float)
        points_object = Points.create(geoh5, name="test-data", vertices=locs)
        locations = InversionLocations(geoh5, params)
        dlocs = locations.get_locations(points_object)
        np.testing.assert_allclose(locs, dlocs)

        xg, yg = np.meshgrid(np.arange(5) + 0.5, np.arange(5) + 0.5)
        locs = np.c_[xg.ravel(), yg.ravel(), np.zeros(25)]
        grid_object = Grid2D.create(
            geoh5,
            origin=[0, 0, 0],
            u_cell_size=1.0,
            v_cell_size=1.0,
            u_count=5,
            v_count=5,
            rotation=0.0,
            dip=0.0,
        )
        dlocs = locations.get_locations(grid_object)
        np.testing.assert_allclose(dlocs, locs)


def test_filter(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    with geoh5.open():
        locations = InversionLocations(geoh5, params)
        test_data = np.array([0, 1, 2, 3, 4, 5])
        locations.mask = np.array([0, 0, 1, 1, 1, 0])
        filtered_data = locations.filter(test_data)
        assert np.all(filtered_data == [2, 3, 4])

        test_data = {"key": test_data}
        filtered_data = locations.filter(test_data)
        assert np.all(filtered_data["key"] == [2, 3, 4])
