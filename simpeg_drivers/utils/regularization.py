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


def cell_neighbors(mesh: TreeMesh) -> np.ndarray:
    """Find all cell neighbors in a TreeMesh."""

    x_neighbors = cell_neighbors_along_axis(mesh, "x")
    x_neighbors_backward = np.fliplr(x_neighbors)
    y_neighbors = cell_neighbors_along_axis(mesh, "y")
    y_neighbors_backward = np.fliplr(y_neighbors)
    max_index = np.max([x_neighbors.max(), y_neighbors.max()])
    if mesh.dim == 3:
        z_neighbors = cell_neighbors_along_axis(mesh, "z")
        z_neighbors_backward = np.fliplr(z_neighbors)
        max_index = np.max([max_index, z_neighbors.max()])

    all_neighbors = []  # Store
    x_adjacent = np.ones(max_index + 1, dtype="int") * -1
    y_adjacent = np.ones(max_index + 1, dtype="int") * -1
    x_adjacent_backward = np.ones(max_index + 1, dtype="int") * -1
    y_adjacent_backward = np.ones(max_index + 1, dtype="int") * -1

    x_adjacent[y_neighbors[:, 0]] = y_neighbors[:, 1]
    y_adjacent[x_neighbors[:, 1]] = x_neighbors[:, 0]

    x_adjacent_backward[y_neighbors_backward[:, 0]] = y_neighbors_backward[:, 1]
    y_adjacent_backward[x_neighbors_backward[:, 1]] = x_neighbors_backward[:, 0]

    all_neighbors += [x_neighbors]
    all_neighbors += [y_neighbors]

    all_neighbors += [np.c_[x_neighbors[:, 0], x_adjacent[x_neighbors[:, 1]]]]
    all_neighbors += [np.c_[x_neighbors[:, 1], x_adjacent[x_neighbors[:, 0]]]]

    all_neighbors += [np.c_[y_adjacent[y_neighbors[:, 0]], y_neighbors[:, 1]]]
    all_neighbors += [np.c_[y_adjacent[y_neighbors[:, 1]], y_neighbors[:, 0]]]

    # Repeat backward for Treemesh
    all_neighbors += [x_neighbors_backward]
    all_neighbors += [y_neighbors_backward]

    all_neighbors += [
        np.c_[
            x_neighbors_backward[:, 0], x_adjacent_backward[x_neighbors_backward[:, 1]]
        ]
    ]
    all_neighbors += [
        np.c_[
            x_neighbors_backward[:, 1], x_adjacent_backward[x_neighbors_backward[:, 0]]
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
    if mesh.dim == 3:
        all_neighbors_z = []
        z_adjacent = np.ones(max_index + 1, dtype="int") * -1
        z_adjacent_backward = np.ones(max_index + 1, dtype="int") * -1

        z_adjacent[z_neighbors[:, 0]] = z_neighbors[:, 1]
        z_adjacent_backward[z_neighbors_backward[:, 0]] = z_neighbors_backward[:, 1]

        all_neighbors_z += [z_neighbors]
        all_neighbors_z += [z_neighbors_backward]

        all_neighbors_z += [np.c_[all_neighbors[:, 0], z_adjacent[all_neighbors[:, 1]]]]
        all_neighbors_z += [np.c_[all_neighbors[:, 1], z_adjacent[all_neighbors[:, 0]]]]

        all_neighbors_z += [
            np.c_[all_neighbors[:, 0], z_adjacent_backward[all_neighbors[:, 1]]]
        ]
        all_neighbors_z += [
            np.c_[all_neighbors[:, 1], z_adjacent_backward[all_neighbors[:, 0]]]
        ]

        # Stack all and keep only unique pairs
        all_neighbors = np.vstack([all_neighbors, np.vstack(all_neighbors_z)])
        all_neighbors = np.unique(all_neighbors, axis=0)

        # Remove all the -1 for TreeMesh
        all_neighbors = all_neighbors[
            (all_neighbors[:, 0] != -1) & (all_neighbors[:, 1] != -1), :
        ]

    return all_neighbors


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
