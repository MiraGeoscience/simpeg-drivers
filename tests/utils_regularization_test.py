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
from discretize import TreeMesh

from simpeg_drivers.utils.regularization import (
    cell_adjacent,
    cell_neighbors_along_axis,
    collect_all_neighbors,
    direction_and_dip,
    ensure_dip_direction_convention,
)


def get_mesh():
    mesh = TreeMesh(h=[[10.0] * 4, [10.0] * 4, [10.0] * 4], diagonal_balance=False)
    mesh.refine(2)
    return mesh


def test_cell_neighbors_along_axis():
    mesh = get_mesh()
    centers = mesh.cell_centers
    neighbors = cell_neighbors_along_axis(mesh, "x")
    assert np.allclose(centers[7], [15.0, 15.0, 15.0])
    assert np.allclose(
        centers[neighbors[neighbors[:, 0] == 7][0][1]], [25.0, 15.0, 15.0]
    )
    assert np.allclose(
        centers[neighbors[neighbors[:, 1] == 7][0][0]], [5.0, 15.0, 15.0]
    )
    neighbors = cell_neighbors_along_axis(mesh, "y")
    assert np.allclose(
        centers[neighbors[neighbors[:, 0] == 7][0][1]], [15.0, 25.0, 15.0]
    )
    assert np.allclose(
        centers[neighbors[neighbors[:, 1] == 7][0][0]], [15.0, 5.0, 15.0]
    )
    neighbors = cell_neighbors_along_axis(mesh, "z")
    assert np.allclose(
        centers[neighbors[neighbors[:, 0] == 7][0][1]], [15.0, 15.0, 25.0]
    )
    assert np.allclose(
        centers[neighbors[neighbors[:, 1] == 7][0][0]], [15.0, 15.0, 5.0]
    )


def test_collect_all_neighbors():
    mesh = get_mesh()
    centers = mesh.cell_centers
    neighbors = [cell_neighbors_along_axis(mesh, k) for k in "xyz"]
    neighbors_bck = [np.fliplr(k) for k in neighbors]
    corners = cell_adjacent(neighbors)
    corners_bck = cell_adjacent(neighbors_bck)
    all_neighbors = collect_all_neighbors(
        neighbors, neighbors_bck, corners, corners_bck
    )
    assert np.allclose(centers[7], [15.0, 15.0, 15.0])
    neighbor_centers = centers[all_neighbors[all_neighbors[:, 0] == 7][:, 1]].tolist()
    assert [5, 5, 5] in neighbor_centers
    assert [15, 5, 5] in neighbor_centers
    assert [25, 5, 5] in neighbor_centers
    assert [5, 15, 5] in neighbor_centers
    assert [15, 15, 5] in neighbor_centers
    assert [25, 15, 5] in neighbor_centers
    assert [5, 25, 5] in neighbor_centers
    assert [15, 25, 5] in neighbor_centers
    assert [25, 25, 5] in neighbor_centers
    assert [5, 5, 15] in neighbor_centers
    assert [15, 5, 15] in neighbor_centers
    assert [25, 5, 15] in neighbor_centers
    assert [5, 15, 15] in neighbor_centers
    assert [25, 15, 15] in neighbor_centers
    assert [5, 25, 15] in neighbor_centers
    assert [15, 25, 15] in neighbor_centers
    assert [25, 25, 15] in neighbor_centers
    assert [5, 5, 25] in neighbor_centers
    assert [15, 5, 25] in neighbor_centers
    assert [25, 5, 25] in neighbor_centers
    assert [5, 15, 25] in neighbor_centers
    assert [15, 15, 25] in neighbor_centers
    assert [25, 15, 25] in neighbor_centers
    assert [5, 25, 25] in neighbor_centers
    assert [15, 25, 25] in neighbor_centers
    assert [25, 25, 25] in neighbor_centers
    assert [15, 15, 15] not in neighbor_centers


def test_ensure_dip_direction_convention():
    # Rotate the vertical unit vector 37 degrees to the west and then 16
    # degrees counter-clockwise about the z-axis.  Should result in a dip
    # direction of 270 - 16 = 254 and a dip of 37.
    Ry = np.array(
        [
            [
                np.cos(np.deg2rad(-37)),
                0,
                np.sin(np.deg2rad(-37)),
            ],
            [0, 1, 0],
            [-np.sin(np.deg2rad(-37)), 0, np.cos(np.deg2rad(-37))],
        ]
    )
    Rz = np.array(
        [
            [np.cos(np.deg2rad(16)), -np.sin(np.deg2rad(16)), 0],
            [np.sin(np.deg2rad(16)), np.cos(np.deg2rad(16)), 0],
            [0, 0, 1],
        ]
    )
    arbitrary_vector = Rz.dot(Ry.dot([0, 0, 1]))

    orientations = np.array(
        [
            [1, 0, 1],
            [0, 1, 1],
            [-1, 0, 1],
            [0, -1, 1],
            [1, 0, np.sqrt(3)],
            [0, 1, np.sqrt(3)],
            [-1, 0, np.sqrt(3)],
            [0, -1, np.sqrt(3)],
            arbitrary_vector.tolist(),
        ]
    )
    dir_dip = ensure_dip_direction_convention(orientations, group_type="3D vector")
    assert np.allclose(dir_dip[:, 0], [90, 0, 270, 180] * 2 + [254])
    assert np.allclose(dir_dip[:, 1], [45] * 4 + [30] * 4 + [37])
