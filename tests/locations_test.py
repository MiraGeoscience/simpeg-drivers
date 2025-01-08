# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                     '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#
#  This file is part of simpeg-drivers.
#
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from geoh5py.objects import Grid2D, Points

from simpeg_drivers.components.locations import InversionLocations
from simpeg_drivers.potential_fields import MagneticVectorParams
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def setup_params(tmp_path):
    geoh5, entity, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=(2,),
        n_electrodes=2,
        n_lines=2,
    )

    geotest = Geoh5Tester(geoh5, tmp_path, "test.geoh5", MagneticVectorParams)
    mesh = geoh5.get_entity("mesh")[0]
    topography_object = geoh5.get_entity("topography")[0]

    geotest.set_param("mesh", str(mesh.uid))
    geotest.set_param("topography_object", str(topography_object.uid))

    return geotest.make()


def test_mask(tmp_path: Path):
    ws, params = setup_params(tmp_path)
    locations = InversionLocations(ws, params)
    loc_mask = [0, 1, 1, 0]
    locations.mask = loc_mask
    assert isinstance(locations.mask, np.ndarray)
    assert locations.mask.dtype == bool
    loc_mask = [0, 1, 2, 3]
    with pytest.raises(ValueError) as excinfo:
        locations.mask = loc_mask
    assert "Badly formed" in str(excinfo.value)


def test_get_locations(tmp_path: Path):
    ws, params = setup_params(tmp_path)
    locs = np.ones((10, 3), dtype=float)
    points_object = Points.create(ws, name="test-data", vertices=locs)
    locations = InversionLocations(ws, params)
    dlocs = locations.get_locations(points_object)
    np.testing.assert_allclose(locs, dlocs)

    xg, yg = np.meshgrid(np.arange(5) + 0.5, np.arange(5) + 0.5)
    locs = np.c_[xg.ravel(), yg.ravel(), np.zeros(25)]
    grid_object = Grid2D.create(
        ws,
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
    ws, params = setup_params(tmp_path)
    locations = InversionLocations(ws, params)
    test_data = np.array([0, 1, 2, 3, 4, 5])
    locations.mask = np.array([0, 0, 1, 1, 1, 0])
    filtered_data = locations.filter(test_data)
    assert np.all(filtered_data == [2, 3, 4])

    test_data = {"key": test_data}
    filtered_data = locations.filter(test_data)
    assert np.all(filtered_data["key"] == [2, 3, 4])


def test_z_from_topo(tmp_path: Path):
    ws, params = setup_params(tmp_path)
    locations = InversionLocations(ws, params)
    locs = locations.set_z_from_topo(np.array([[0.0, 0.0, 0.0]]))
    assert np.isclose(locs[0, 2], 49.91677)

    params.topography = 320.0
    locations = InversionLocations(ws, params)
    locs = locations.set_z_from_topo(np.array([[315674, 6070832, 0]]))
    assert locs[0, 2] == 320.0
