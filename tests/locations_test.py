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
from geoh5py import Workspace
from geoh5py.objects import Curve, Grid2D, Points
from scipy.spatial import ConvexHull

from simpeg_drivers.components.locations import InversionLocations
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import MVIInversionOptions
from simpeg_drivers.utils.utils import tile_locations
from tests.testing_utils import Geoh5Tester, setup_inversion_workspace


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
    params = MVIInversionOptions.build(
        geoh5=geoh5,
        data_object=survey,
        tmi_channel=tmi_channel,
        tmi_uncertainty=1.0,
        topography_object=topography,
        mesh=model.parent,
        starting_model=model,
        inducing_field_strength=50000.0,
        inducing_field_inclination=60.0,
        inducing_field_declination=30.0,
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


def test_tile_locations_equal_area(tmp_path: Path):
    with Workspace.create(tmp_path / f"{__name__}.geoh5") as ws:
        grid_x, grid_y = np.meshgrid(np.arange(100), np.arange(100))
        choices = np.c_[grid_x.ravel(), grid_y.ravel(), np.zeros(grid_x.size)]
        inds = np.random.randint(0, 10000, 1000)
        pts = Points.create(
            ws,
            name="test-points",
            vertices=choices[inds],
        )
        tiles = tile_locations(pts.vertices, n_tiles=8, equal_area=True)

        values = np.zeros(pts.n_vertices)
        areas = []
        for ind, tile in enumerate(tiles):
            values[tile] = ind
            hull = ConvexHull(pts.vertices[tile, :2])
            areas.append(hull.area)  # pylint: disable=no-member

        pts.add_data(
            {
                "values": {
                    "values": values,
                }
            }
        )
        assert np.std(areas) / np.mean(areas) < 0.05, "Areas of tiles are not equal"


def test_tile_locations_labels(tmp_path: Path):
    stn = np.arange(0, 10000, 1000)
    x_locs = np.kron(stn, np.ones(100)) + np.random.randn(1000) * 10
    y_locs = np.kron(np.ones(len(stn)), np.arange(100) * 1000)
    locations = np.c_[x_locs, y_locs, np.random.randn(len(x_locs)) * 100]
    line_id = np.kron(np.arange(len(stn)), np.ones(100))

    with Workspace.create(tmp_path / f"{__name__}.geoh5") as ws:
        curve = Curve.create(
            ws,
            vertices=locations,
            parts=line_id,
        )

        # Test that the tiles are assigned to the correct parts
        tiles = tile_locations(curve.vertices, n_tiles=10, labels=curve.parts)
        values = np.zeros(curve.n_vertices)
        single_part = []
        for ind, tile in enumerate(tiles):
            values[tile] = ind
            single_part.append(len(set(curve.parts[tile])) == 1)

        assert all(single_part)

        curve.add_data(
            {
                "values": {
                    "values": values,
                }
            }
        )

        # Repeat with fewer tiles than parts (at most grab two lines)
        tiles = tile_locations(curve.vertices, n_tiles=5, labels=curve.parts)
        values = np.zeros(curve.n_vertices)
        two_parts = []
        for ind, tile in enumerate(tiles):
            values[tile] = ind
            two_parts.append(len(set(curve.parts[tile])) == 2)

        assert all(two_parts)
        assert (
            len({len(tile) for tile in tiles}) == 1
        )  # All tiles have the same number of vertices
        with pytest.raises(ValueError, match="Labels array must have the same length"):
            tile_locations(curve.vertices, n_tiles=8, labels=curve.parts[:-1])
