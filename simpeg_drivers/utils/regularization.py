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
from geoapps_utils.utils.transformations import (
    cartesian_normal_to_direction_and_dip,
    x_rotation_matrix,
    z_rotation_matrix,
)
from geoh5py.groups import PropertyGroup
from geoh5py.groups.property_group_type import GroupTypeEnum
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
    stencil_indices = jth_neighbor[np.argsort(ith_neighbor)].reshape((-1, 2))

    return np.sort(stencil_indices, axis=1)


def clean_index_array(index_array: np.ndarray) -> np.ndarray:
    """
    Remove duplicate rows or rows with -1 in index array.

    :param index_array: Array of index pairs.

    :return: Cleaned array of index pairs.
    """
    array = np.unique(index_array, axis=0)

    # Remove all the -1 for TreeMesh
    mask = ~np.any(array == -1, axis=1)
    return array[mask, :]


def collect_all_neighbors(
    neighbors: list[np.ndarray],
    neighbors_backwards: list[np.ndarray],
    adjacent: np.ndarray,
    adjacent_backwards: np.ndarray,
) -> list[np.ndarray]:
    """
    Collect all neighbors for cells in the mesh.

    :param neighbors: Direct neighbors in each principle axes.
    :param neighbors_backwards: Direct neighbors in reverse order.
    :param adjacent: Adjacent neighbors (corners).
    :param adjacent_backwards: Adjacent neighbors in reverse order.

    :return: List of arrays of cell neighbors in all principle directions. List
    length is 8 for 2D meshes and 26 for 3D meshes.
    """
    neighbours_lists = [
        neighbors[0],  # [i+1, j]
        neighbors[1],  # [i, j+1]
        np.c_[neighbors[0][:, 0], adjacent[:, 0][neighbors[0][:, 1]]],  # [i+1, j+1]
        np.c_[neighbors[0][:, 1], adjacent[:, 0][neighbors[0][:, 0]]],  # [i-1, j+1]
        np.c_[adjacent[:, 1][neighbors[1][:, 1]], neighbors[1][:, 0]],  # [i+1, j-1]
        # Repeat backward for Treemesh
        neighbors_backwards[0],  # [i-1, j]
        neighbors_backwards[1],  # [i, j-1]
        np.c_[
            neighbors_backwards[0][:, 0],
            adjacent_backwards[:, 0][neighbors_backwards[0][:, 1]],
        ],  # [i-1, j-1]
    ]

    # Stack all and keep only unique pairs
    all_neighbors = [clean_index_array(elem) for elem in neighbours_lists]

    # Use all the neighbours on the xy plane to find neighbours in z
    if len(neighbors) == 3:
        max_index = np.vstack(all_neighbors).max() + 1
        neigh_z = np.c_[np.arange(max_index), np.full(max_index, -1)].astype("int")
        neigh_z[neighbors[2][:, 0], 1] = neighbors[2][:, 1]

        neigh_z_back = np.c_[np.arange(max_index), np.full(max_index, -1)].astype("int")
        neigh_z_back[neighbors_backwards[2][:, 0], 1] = neighbors_backwards[2][:, 1]

        z_list = [
            neighbors[2],  # z-positive
            neighbors_backwards[2],  # z-negative
        ]
        for elem in all_neighbors:  # All x and y neighbors
            z_list.append(
                clean_index_array(
                    np.c_[elem[:, 0], neigh_z[elem[:, 1], 1]]
                )  # [i, j, k+1]
            )
            z_list.append(
                clean_index_array(
                    np.c_[elem[:, 0], neigh_z_back[elem[:, 1], 1]]
                )  # [i, j, k-1]
            )

        all_neighbors += z_list

    return all_neighbors


def cell_adjacent(mesh: TreeMesh, backward: bool = False) -> list[np.ndarray]:
    """
    Find all adjacent (corner) cells from cell neighbor array.

    :param mesh: Input TreeMesh
    :param backward: If True, find the opposite corner neighbors.

    :return: Array of adjacent cell neighbors.
    """
    neighbors = [
        cell_neighbors_along_axis(mesh, "x"),
        cell_neighbors_along_axis(mesh, "y"),
    ]

    if backward:
        neighbors = [np.fliplr(k) for k in neighbors]

    corners = -1 * np.ones((mesh.n_cells, 2), dtype="int")

    corners[neighbors[1][:, 0], 0] = neighbors[1][:, 1]
    corners[neighbors[0][:, 1], 1] = neighbors[0][:, 0]

    return corners


def cell_neighbors_lists(mesh: TreeMesh) -> list[np.ndarray]:
    """
    Find cell neighbors in all directions.

    :param mesh: Input TreeMesh.

    :return: List of arrays of cell neighbors in all principle directions. List
    length is 8 for 2D meshes and 26 for 3D meshes.
    """
    neighbors = [
        cell_neighbors_along_axis(mesh, "x"),
        cell_neighbors_along_axis(mesh, "y"),
    ]

    if mesh.dim == 3:
        neighbors.append(cell_neighbors_along_axis(mesh, "z"))

    neighbors_backwards = [np.fliplr(k) for k in neighbors]
    corners = cell_adjacent(mesh)
    corners_backwards = cell_adjacent(mesh, backward=True)

    return collect_all_neighbors(
        neighbors, neighbors_backwards, corners, corners_backwards
    )


def cell_neighbors(mesh: TreeMesh) -> np.ndarray:
    """
    Find all cell neighbors in a TreeMesh.

    :param mesh: Input TreeMesh.

    :return: Array of unique and sorted cell neighbor pairs.
    """
    neighbors_lists = cell_neighbors_lists(mesh)
    return np.unique(np.vstack(neighbors_lists), axis=1)


def rotate_xz_2d(mesh: TreeMesh, phi: np.ndarray) -> ssp.csr_matrix:
    """
    Create a 2d ellipsoidal rotation matrix for the xz plane.

    :param mesh: TreeMesh used to adjust angle of rotation to
        compensate for cell aspect ratio.
    :param phi: Angle in radians for clockwise rotation about the
        y-axis (xz plane).

    :return: Sparse rotation matrix
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

    :return: Sparse rotation matrix
    """
    hy = mesh.h_gridded[:, 1]
    hz = mesh.h_gridded[:, 2]
    theta = -np.arctan2((np.sin(theta) / hz), (np.cos(theta) / hy))

    return x_rotation_matrix(theta)


def rotate_xy_3d(mesh: TreeMesh, phi: np.ndarray) -> ssp.csr_matrix:
    """
    Create a 3D ellipsoidal rotation matrix for the xy plane.

    :param mesh: TreeMesh used to adjust angle of rotation to
        compensate for cell aspect ratio.
    :param phi: Angle in radians for clockwise rotation about the
        z-axis (xy plane).

    :return: Sparse rotation matrix
    """
    hx = mesh.h_gridded[:, 0]
    hy = mesh.h_gridded[:, 1]
    phi = -np.arctan2((np.sin(phi) / hy), (np.cos(phi) / hx))

    return z_rotation_matrix(phi)


def get_cell_normals(n_cells: int, axis: str, outward: bool, dim: int) -> np.ndarray:
    """
    Returns cell normals for given axis and all cells.

    :param n_cells: Number of cells in the mesh.
    :param axis: Cartesian axis (one of 'x', 'y', or 'z'
    :param outward: Direction of the normal. True for outward facing,
        False for inward facing normals.
    :param dim: Dimension of the mesh. Either 2 for drape model or 3
        for octree.

    :return: Array of cell normals.
    """

    ind = 1 if outward else -1

    if axis == "x":
        n = np.c_[ind, 0] if dim == 2 else np.c_[ind, 0, 0]
        normals = np.kron(np.ones(n_cells), n)
    elif axis == "y":
        n = np.c_[0, ind] if dim == 2 else np.c_[0, ind, 0]
        normals = np.kron(np.ones(n_cells), n)
    elif axis == "z":
        n = np.c_[0, ind] if dim == 2 else np.c_[0, 0, ind]
        normals = np.kron(np.ones(n_cells), n)
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
    grad = ssp.csr_matrix(
        (volumes, (neighbors[:, 0], neighbors[:, 1])), shape=(n_cells, n_cells)
    )

    # Normalize rows
    vol = mkvc(grad.sum(axis=1))
    vol[vol > 0] = 1.0 / vol[vol > 0]
    grad = -sdiag(vol) * grad

    diag = np.ones(n_cells)
    diag[vol == 0] = 0
    grad = sdiag(diag) + grad

    return grad


def rotated_gradient(
    mesh: TreeMesh,
    neighbors: np.ndarray,
    axis: str,
    dip: np.ndarray,
    direction: np.ndarray,
    forward: bool = True,
) -> ssp.csr_matrix:
    """
    Calculated rotated gradient operator using unit partial volumes.

    :param mesh: Input TreeMesh.
    :param neighbors: Cell neighbors array.
    :param axis: Regularization axis.
    :param dip: Angle in radians for rotation from the horizon.
    :param direction: Angle in radians for rotation about the z-axis.
    :param forward: Whether to use forward or backward difference for
        derivative approximations.
    """

    n_cells = mesh.n_cells
    dim = mesh.dim
    if any(len(k) != n_cells for k in [dip, direction]):
        raise ValueError(
            "Input angle arrays are not the same size as the number of "
            "cells in the mesh."
        )

    normals = get_cell_normals(n_cells, axis, forward, dim)
    if dim == 3:
        Rx = rotate_yz_3d(mesh, dip)
        Rz = rotate_xy_3d(mesh, direction)
        rotated_normals = (Rz * (Rx * normals.T)).reshape(n_cells, dim)
    elif dim == 2:
        Ry = rotate_xz_2d(mesh, dip)
        rotated_normals = (Ry * normals.T).reshape(n_cells, dim)

    volumes, neighbors = partial_volumes(
        mesh,
        neighbors,
        rotated_normals,  # pylint: disable=possibly-used-before-assignment
    )

    unit_grad = gradient_operator(neighbors, volumes, n_cells)

    return unit_grad


def ensure_dip_direction_convention(
    orientations: np.ndarray, group_type: str
) -> np.ndarray:
    """
    Ensure orientations array has dip and direction convention.

    :param orientations: Array of orientations.  Either n * 2 if Strike & dip
        or Dip direction & dip group_type, or n * 3 if 3D Vector group_type defining the normal of the dipping plane.
    :param group_type as specified in geoh5py.GroupTypeEnum.
    """

    if group_type == GroupTypeEnum.VECTOR:
        orientations = np.rad2deg(cartesian_normal_to_direction_and_dip(orientations))

    if group_type in [GroupTypeEnum.STRIKEDIP]:
        orientations[:, 0] = 90.0 + orientations[:, 0]

    return orientations


def direction_and_dip(property_group: PropertyGroup) -> list[np.ndarray]:
    """Conversion of orientation group to direction and dip."""

    group_type = property_group.property_group_type
    if group_type not in [
        GroupTypeEnum.VECTOR,
        GroupTypeEnum.STRIKEDIP,
        GroupTypeEnum.DIPDIR,
    ]:
        raise ValueError(
            "Property group does not contain orientation data. "
            "Type must be one of '3D vector', 'Strike & dip', or "
            "'Dip direction & dip'."
        )

    orientations = np.vstack(
        [property_group.parent.get_data(k)[0].values for k in property_group.properties]
    ).T

    return ensure_dip_direction_convention(orientations, group_type)


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
    mesh = function.regularization_mesh
    axes = "xyz" if mesh.dim == 3 else "xz"

    h_cell = mesh.mesh.h_gridded[:, axes.find(axis)]

    unit_grad_op = rotated_gradient(mesh.mesh, neighbors, axis, dip, direction, forward)

    vol_avg_op = abs(unit_grad_op)
    vol_avg_op.data = (
        vol_avg_op.data * mesh.mesh.cell_volumes[unit_grad_op.nonzero()[1]]
    )

    grad_op_active = mesh.Pac.T @ (unit_grad_op @ mesh.Pac)

    # Remove extra partial volume from missing neighbors
    row_sum = np.asarray(grad_op_active.sum(axis=1)).ravel()
    grad_op_active -= sdiag(row_sum)

    vol_avg_op = mesh.Pac.T @ (vol_avg_op @ mesh.Pac)
    active_faces = grad_op_active.max(axis=1).toarray().ravel() != 0

    vol_avg_op = vol_avg_op[active_faces, :]
    vol_avg_op = sdiag(np.asarray(vol_avg_op.sum(axis=1)).ravel() ** -1) @ vol_avg_op
    h_op = sdiag(vol_avg_op @ (mesh.Pac.T @ h_cell**-1.0))
    grad_op = h_op @ grad_op_active[active_faces, :]

    setattr(
        mesh,
        f"_cell_gradient_{function.orientation}",
        grad_op,
    )
    setattr(
        mesh,
        f"_aveCC2F{function.orientation}",
        vol_avg_op,
    )

    return function
