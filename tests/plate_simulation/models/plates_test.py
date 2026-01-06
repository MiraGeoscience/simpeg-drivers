# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.utils.transformations import rotate_xyz
from geoh5py import Workspace

from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.models.options import PlateOptions
from simpeg_drivers.plate_simulation.models.parametric import Plate


def are_collocated(pts1, pts2):
    truth = []
    for loc in pts1:
        truth.append(any(np.allclose(loc, k) for k in pts2))

    return np.all(truth)


def vertical_east_striking_plate():
    params = PlateOptions(
        name="my plate",
        plate=1.0,
        elevation=0.0,
        width=10.0,
        strike_length=1000.0,
        dip_length=500.0,
        dip=90.0,
        dip_direction=0.0,
    )
    plate = Plate(params)

    return plate.surface


def test_vertical_east_striking_plate():
    vertical_east_striking = vertical_east_striking_plate()
    assert vertical_east_striking.vertices is not None
    assert vertical_east_striking.extent is not None
    assert np.isclose(
        vertical_east_striking.extent[1, 0] - vertical_east_striking.extent[0, 0],
        1000.0,
    )
    assert np.isclose(
        vertical_east_striking.extent[1, 1] - vertical_east_striking.extent[0, 1],
        10.0,
    )
    assert np.isclose(
        vertical_east_striking.extent[1, 2] - vertical_east_striking.extent[0, 2],
        500.0,
    )
    assert (
        vertical_east_striking.vertices[:, 0].mean() == 0.0  # pylint: disable=no-member
    )
    assert (
        vertical_east_striking.vertices[:, 1].mean() == 0.0  # pylint: disable=no-member
    )
    assert (
        vertical_east_striking.vertices[:, 2].mean() == 0.0  # pylint: disable=no-member
    )


def test_dipping_plates_all_quadrants():
    reference = vertical_east_striking_plate()

    for dip_direction in np.arange(0.0, 361.0, 45.0):
        for dip in [20.0, 70.0]:
            params = PlateOptions(
                name=f"plate dipping {dip} at {dip_direction}",
                plate=1.0,
                elevation=0.0,
                width=10.0,
                strike_length=1000.0,
                dip_length=500.0,
                dip=dip,
                dip_direction=dip_direction,
                reference="center",
            )

            plate = Plate(params)
            surface = plate.surface
            locs = rotate_xyz(surface.vertices, [0.0, 0.0, 0.0], dip_direction, 0.0)
            locs = rotate_xyz(locs, [0.0, 0.0, 0.0], 0.0, dip - 90.0)
            assert np.allclose(locs, reference.vertices)


def test_replicate_even(tmp_path):
    workspace = Workspace.create(tmp_path / f"{__name__}.geoh5")
    options = PlateOptions(
        name="test",
        plate=1.0,
        width=1.0,
        strike_length=1.0,
        dip_length=1.0,
        elevation=1.0,
    )
    plate = Plate(options, (0, 0, 0), workspace=workspace)
    plates = PlateSimulationDriver.replicate(plate, 2, 10.0, 90.0)
    assert plates[0].surface.vertices is not None
    assert plates[1].surface.vertices is not None
    assert plates[0].params.name == "test offset 1"
    assert np.allclose(
        plates[0].surface.vertices.mean(axis=0), np.array([-5.0, 0.0, 0.0])
    )
    assert plates[1].params.name == "test offset 2"
    assert np.allclose(
        plates[1].surface.vertices.mean(axis=0), np.array([5.0, 0.0, 0.0])
    )


def test_replicate_odd(tmp_path):
    workspace = Workspace.create(tmp_path / f"{__name__}.geoh5")
    options = PlateOptions(
        name="test",
        plate=1.0,
        width=1.0,
        strike_length=1.0,
        dip_length=1.0,
        elevation=1.0,
    )
    plate = Plate(options, (0, 0, 0), workspace=workspace)
    plates = PlateSimulationDriver.replicate(plate, 3, 5.0, 0.0)
    assert plates[0].surface.vertices is not None
    assert plates[1].surface.vertices is not None
    assert plates[2].surface.vertices is not None
    assert np.allclose(
        plates[0].surface.vertices.mean(axis=0), np.array([0.0, -5.0, 0.0])
    )
    assert np.allclose(
        plates[1].surface.vertices.mean(axis=0), np.array([0.0, 0.0, 0.0])
    )
    assert np.allclose(
        plates[2].surface.vertices.mean(axis=0), np.array([0.0, 5.0, 0.0])
    )
