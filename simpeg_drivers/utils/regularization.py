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
import scipy.sparse as ssp
from discretize import TreeMesh
from simpeg.regularization import SparseSmoothness
from simpeg.utils import mkvc, sdiag


def cell_neighbors_along_axis(mesh: TreeMesh, axis: str) -> np.ndarray:
    """
    Get adjacent cells along provided axis for all cells in the mesh

    :param mesh: Input TreeMesh.
    :param axis: Cartesian axis along which to find neighbors.  Must be
        'x', 'y', or 'z'.
    """

    if axis not in "xyz":
        raise ValueError("Argument 'axis' must be one of 'x', 'y', or 'z'.")

    if isinstance(mesh, TreeMesh):
        stencil = getattr(mesh, f"stencil_cell_gradient_{axis}")
    else:
        stencil = getattr(mesh, f"cell_gradient_{axis}")

    ith_neighbor, jth_neighbor, _ = ssp.find(stencil)
    n_stencils = int(ith_neighbor.shape[0] / 2)
    stencil_indices = jth_neighbor[np.argsort(ith_neighbor)].reshape((n_stencils, 2))

    return np.sort(stencil_indices, axis=1)


def collect_all_neighbors(
    neighbors: list[np.ndarray],
    neighbors_backwards: list[np.ndarray],
    adjacent: list[np.ndarray],
    adjacent_backwards: list[np.ndarray],
) -> np.ndarray:
    """
    Collect all neighbors for cells in the mesh.

    :param neighbors: Direct neighbors in each principle axes.
    :param neighbors_backwards: Direct neighbors in reverse order.
    :param adjacent: Adjacent neighbors (corners).
    :param adjacent_backwards: Adjacent neighbors in reverse order.
    """
    all_neighbors = []  # Store

    all_neighbors += [neighbors[0]]
    all_neighbors += [neighbors[1]]

    all_neighbors += [np.c_[neighbors[0][:, 0], adjacent[0][neighbors[0][:, 1]]]]
    all_neighbors += [np.c_[neighbors[0][:, 1], adjacent[0][neighbors[0][:, 0]]]]

    all_neighbors += [np.c_[adjacent[1][neighbors[1][:, 0]], neighbors[1][:, 1]]]
    all_neighbors += [np.c_[adjacent[1][neighbors[1][:, 1]], neighbors[1][:, 0]]]

    # Repeat backward for Treemesh
    all_neighbors += [neighbors_backwards[0]]
    all_neighbors += [neighbors_backwards[1]]

    all_neighbors += [
        np.c_[
            neighbors_backwards[0][:, 0],
            adjacent_backwards[0][neighbors_backwards[0][:, 1]],
        ]
    ]
    all_neighbors += [
        np.c_[
            neighbors_backwards[0][:, 1],
            adjacent_backwards[0][neighbors_backwards[0][:, 0]],
        ]
    ]

    # Stack all and keep only unique pairs
    all_neighbors = np.vstack(all_neighbors)
    all_neighbors = np.unique(all_neighbors, axis=0)

    # Remove all the -1 for TreeMesh
    all_neighbors = all_neighbors[
        (all_neighbors[:, 0] != -1) & (all_neighbors[:, 1] != -1), :
    ]

    # Use all the neighbours on the xy plane to find neighbours in z
    if len(neighbors) == 3:
        all_neighbors_z = []

        all_neighbors_z += [neighbors[2]]
        all_neighbors_z += [neighbors_backwards[2]]

        all_neighbors_z += [
            np.c_[all_neighbors[:, 0], adjacent[2][all_neighbors[:, 1]]]
        ]
        all_neighbors_z += [
            np.c_[all_neighbors[:, 1], adjacent[2][all_neighbors[:, 0]]]
        ]

        all_neighbors_z += [
            np.c_[all_neighbors[:, 0], adjacent_backwards[2][all_neighbors[:, 1]]]
        ]
        all_neighbors_z += [
            np.c_[all_neighbors[:, 1], adjacent_backwards[2][all_neighbors[:, 0]]]
        ]

        # Stack all and keep only unique pairs
        all_neighbors = np.vstack([all_neighbors, np.vstack(all_neighbors_z)])
        all_neighbors = np.unique(all_neighbors, axis=0)

        # Remove all the -1 for TreeMesh
        all_neighbors = all_neighbors[
            (all_neighbors[:, 0] != -1) & (all_neighbors[:, 1] != -1), :
        ]

    return all_neighbors


def cell_adjacent(neighbors: list[np.ndarray]) -> list[np.ndarray]:
    """Find all adjacent cells (corners) from cell neighbor array."""

    dim = len(neighbors)
    max_index = np.max(np.vstack(neighbors))
    corners = -1 * np.ones((dim, max_index + 1), dtype="int")

    corners[0, neighbors[1][:, 0]] = neighbors[1][:, 1]
    corners[1, neighbors[0][:, 1]] = neighbors[0][:, 0]
    if dim == 3:
        corners[2, neighbors[2][:, 0]] = neighbors[2][:, 1]

    return [np.array(k) for k in corners.tolist()]


def cell_neighbors(mesh: TreeMesh) -> np.ndarray:
    """Find all cell neighbors in a TreeMesh."""

    neighbors = []
    neighbors.append(cell_neighbors_along_axis(mesh, "x"))
    neighbors.append(cell_neighbors_along_axis(mesh, "y"))
    if mesh.dim == 3:
        neighbors.append(cell_neighbors_along_axis(mesh, "z"))

    neighbors_backwards = [np.fliplr(k) for k in neighbors]
    corners = cell_adjacent(neighbors)
    corners_backwards = cell_adjacent(neighbors_backwards)

    return collect_all_neighbors(
        neighbors, neighbors_backwards, corners, corners_backwards
    )


def rotate_xz_2d(mesh: TreeMesh, phi: np.ndarray) -> ssp.csr_matrix:
    """
    Create a 2d ellipsoidal rotation matrix for the xz plane.

    :param mesh: TreeMesh used to adjust angle of rotation to
        compensate for cell aspect ratio.
    :param phi: Angle in radians for clockwise rotation about the
        y-axis (xz plane).
    """

    if mesh.dim != 2:
        raise ValueError("Must pass a 2 dimensional mesh.")

    n_cells = len(phi)
    hx = mesh.h_gridded[:, 0]
    hz = mesh.h_gridded[:, 1]
    phi = -np.arctan2((np.sin(phi) / hz), (np.cos(phi) / hx))

    rza = mkvc(np.c_[np.cos(phi), np.cos(phi)].T)
    rzb = mkvc(np.c_[np.sin(phi), np.zeros(n_cells)].T)
    rzc = mkvc(np.c_[-np.sin(phi), np.zeros(n_cells)].T)
    Ry = ssp.diags([rzb[:-1], rza, rzc[:-1]], [-1, 0, 1])

    return Ry


def rotate_yz_3d(mesh: TreeMesh, theta: np.ndarray) -> ssp.csr_matrix:
    """
    Create a 3D ellipsoidal rotation matrix for the yz plane.

    :param mesh: TreeMesh used to adjust angle of rotation to
        compensate for cell aspect ratio.
    :param theta: Angle in radians for clockwise rotation about the
        x-axis (yz plane).
    """

    n_cells = len(theta)
    hy = mesh.h_gridded[:, 1]
    hz = mesh.h_gridded[:, 2]
    theta = -np.arctan2((np.sin(theta) / hz), (np.cos(theta) / hy))

    rxa = mkvc(np.c_[np.ones(n_cells), np.cos(theta), np.cos(theta)].T)
    rxb = mkvc(np.c_[np.zeros(n_cells), np.sin(theta), np.zeros(n_cells)].T)
    rxc = mkvc(np.c_[np.zeros(n_cells), -np.sin(theta), np.zeros(n_cells)].T)
    Rx = ssp.diags([rxb[:-1], rxa, rxc[:-1]], [-1, 0, 1])

    return Rx


def rotate_xy_3d(mesh: TreeMesh, phi: np.ndarray) -> ssp.csr_matrix:
    """
    Create a 3D ellipsoidal rotation matrix for the xy plane.

    :param mesh: TreeMesh used to adjust angle of rotation to
        compensate for cell aspect ratio.
    :param phi: Angle in radians for clockwise rotation about the
        z-axis (xy plane).
    """
    n_cells = len(phi)
    hx = mesh.h_gridded[:, 0]
    hy = mesh.h_gridded[:, 1]
    phi = -np.arctan2((np.sin(phi) / hy), (np.cos(phi) / hx))

    rza = mkvc(np.c_[np.cos(phi), np.cos(phi), np.ones(n_cells)].T)
    rzb = mkvc(np.c_[np.sin(phi), np.zeros(n_cells), np.zeros(n_cells)].T)
    rzc = mkvc(np.c_[-np.sin(phi), np.zeros(n_cells), np.zeros(n_cells)].T)
    Rz = ssp.diags([rzb[:-1], rza, rzc[:-1]], [-1, 0, 1])

    return Rz


def get_cell_normals(n_cells: int, axis: str, outward: bool) -> np.ndarray:
    """
    Returns cell normals for given axis and all cells.

    :param n_cells: Number of cells in the mesh.
    :param axis: Cartesian axis (one of 'x', 'y', or 'z'
    :param outward: Direction of the normal. True for outward facing,
        False for inward facing normals.
    """

    ind = 1 if outward else -1

    if axis == "x":
        normals = np.kron(np.ones(n_cells), np.c_[ind, 0, 0])
    elif axis == "y":
        normals = np.kron(np.ones(n_cells), np.c_[0, ind, 0])
    elif axis == "z":
        normals = np.kron(np.ones(n_cells), np.c_[0, 0, ind])
    else:
        raise ValueError("Axis must be one of 'x', 'y', or 'z'.")

    return normals


def get_cell_corners(
    mesh: TreeMesh,
    neighbors: np.ndarray,
    normals: np.ndarray,
) -> list[np.ndarray]:
    """
    Return the bottom southwest and top northeast nodes of all cells.

    :param mesh: Input TreeMesh.
    :param neighbors: Cell neighbors array.
    :param normals: Cell normals array.
    """

    bottom_southwest = (
        mesh.gridCC[neighbors[:, 0], :]
        - mesh.h_gridded[neighbors[:, 0], :] / 2
        + normals[neighbors[:, 0], :] * mesh.h_gridded[neighbors[:, 0], :]
    )
    top_northeast = (
        mesh.gridCC[neighbors[:, 0], :]
        + mesh.h_gridded[neighbors[:, 0], :] / 2
        + normals[neighbors[:, 0], :] * mesh.h_gridded[neighbors[:, 0], :]
    )

    return [bottom_southwest, top_northeast]


def get_neighbor_corners(mesh: TreeMesh, neighbors: np.ndarray):
    """
    Return the bottom southwest and top northeast corners.

    :param mesh: Input TreeMesh.
    :param neighbors: Cell neighbors array.
    """

    bottom_southwest = (
        mesh.gridCC[neighbors[:, 1], :] - mesh.h_gridded[neighbors[:, 1], :] / 2
    )
    top_northeast = (
        mesh.gridCC[neighbors[:, 1], :] + mesh.h_gridded[neighbors[:, 1], :] / 2
    )

    corners = [bottom_southwest, top_northeast]

    return corners


def partial_volumes(
    mesh: TreeMesh, neighbors: np.ndarray, normals: np.ndarray
) -> np.ndarray:
    """
    Compute partial volumes created by intersecting rotated and unrotated cells.

    :param mesh: Input TreeMesh.
    :param neighbors: Cell neighbors array.
    :param normals: Cell normals array.
    """
    cell_corners = get_cell_corners(mesh, neighbors, normals)
    neighbor_corners = get_neighbor_corners(mesh, neighbors)

    volumes = np.ones(neighbors.shape[0])
    for i in range(mesh.dim):
        volumes *= np.max(
            [
                np.min([neighbor_corners[1][:, i], cell_corners[1][:, i]], axis=0)
                - np.max([neighbor_corners[0][:, i], cell_corners[0][:, i]], axis=0),
                np.zeros(neighbors.shape[0]),
            ],
            axis=0,
        )

    # Remove all rows of zero
    ind = (volumes > 0) * (neighbors[:, 0] != neighbors[:, 1])
    neighbors = neighbors[ind, :]
    volumes = volumes[ind]

    return volumes, neighbors


def gradient_operator(
    neighbors: np.ndarray, volumes: np.ndarray, n_cells: int
) -> ssp.csr_matrix:
    """
    Assemble the sparse gradient operator.

    :param neighbors: Cell neighbor array.
    :param volumes: Partial volume array.
    :param n_cells: Number of cells in mesh.
    """
    Grad = ssp.csr_matrix(
        (volumes, (neighbors[:, 0], neighbors[:, 1])), shape=(n_cells, n_cells)
    )

    # Normalize rows
    Vol = mkvc(Grad.sum(axis=1))
    Vol[Vol > 0] = 1.0 / Vol[Vol > 0]
    Grad = -sdiag(Vol) * Grad

    diag = np.ones(n_cells)
    diag[Vol == 0] = 0
    Grad = sdiag(diag) + Grad

    return Grad


def rotated_gradient(
    mesh: TreeMesh,
    neighbors: np.ndarray,
    axis: str,
    dip: np.ndarray,
    direction: np.ndarray,
    forward: bool = True,
) -> ssp.csr_matrix:
    """
    Calculated rotated gradient operator using partial volumes.

    :param mesh: Input TreeMesh.
    :param neighbors: Cell neighbors array.
    :param axis: Regularization axis.
    :param dip: Angle in radians for rotation from the horizon.
    :param direction: Angle in radians for rotation about the z-axis.
    :param forward: Whether to use forward or backward difference for
        derivative approximations.
    """

    n_cells = mesh.n_cells
    if any(len(k) != n_cells for k in [dip, direction]):
        raise ValueError(
            "Input angle arrays are not the same size as the number of "
            "cells in the mesh."
        )

    Rx = rotate_yz_3d(mesh, dip)
    Rz = rotate_xy_3d(mesh, direction)
    normals = get_cell_normals(n_cells, axis, forward)
    rotated_normals = (Rz * (Rx * normals.T)).reshape(n_cells, mesh.dim)
    volumes, neighbors = partial_volumes(mesh, neighbors, rotated_normals)

    unit_grad = gradient_operator(neighbors, volumes, n_cells)
    return sdiag(1 / mesh.h_gridded[:, "xyz".find(axis)]) @ unit_grad


def set_rotated_operators(
    function: SparseSmoothness,
    neighbors: np.ndarray,
    axis: str,
    dip: np.ndarray,
    direction: np.ndarray,
    forward: bool = True,
) -> SparseSmoothness:
    """
    Calculated rotated gradient operator using partial volumes.

    :param function: Smoothness regularization to change operator for.
    :param neighbors: Cell neighbors array.
    :param axis: Regularization axis.
    :param dip: Angle in radians for rotation from the horizon.
    :param direction: Angle in radians for rotation about the z-axis.
    :param forward: Whether to use forward or backward difference for
        derivative approximations.
    """
    grad_op = rotated_gradient(
        function.regularization_mesh.mesh, neighbors, axis, dip, direction, forward
    )
    grad_op_active = function.regularization_mesh.Pac.T @ (
        grad_op @ function.regularization_mesh.Pac
    )
    active_faces = grad_op_active.max(axis=1).toarray().ravel() > 0

    setattr(
        function.regularization_mesh,
        f"_cell_gradient_{function.orientation}",
        grad_op_active[active_faces, :],
    )
    setattr(
        function.regularization_mesh,
        f"_aveCC2F{function.orientation}",
        sdiag(np.ones(function.regularization_mesh.n_cells))[active_faces, :],
    )

    return function
