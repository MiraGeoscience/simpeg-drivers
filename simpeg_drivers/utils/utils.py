#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.
#
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import numpy as np
from geoapps_utils.conversions import string_to_numeric
from geoh5py import Workspace
from geoh5py.data import FilenameData
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import DrapeModel, Octree
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.spatial import Delaunay, cKDTree

from simpeg_drivers.utils.mesh import cell_size_z

if TYPE_CHECKING:
    pass


def get_inversion_output(h5file: str | Workspace, inversion_group: str | UUID):
    """
    Recover inversion iterations from a ContainerGroup comments.
    """
    if isinstance(h5file, Workspace):
        workspace = h5file
    else:
        workspace = Workspace(h5file)

    group = workspace.get_entity(inversion_group)[0]

    if not isinstance(group, SimPEGGroup):
        raise IndexError(
            f"BaseInversion group {inversion_group} could not be found in the target geoh5 {h5file}"
        )

    outfile = group.get_entity("SimPEG.out")[0]

    if not isinstance(outfile, FilenameData) or outfile.values is None:
        raise IndexError(f"SimPEG.out could not be found in the target geoh5 {h5file}")

    out = list(outfile.values.decode("utf-8").replace("\r", "").split("\n"))[:-1]
    cols = out.pop(0).split(" ")

    formatted = [[string_to_numeric(k) for k in line.split(" ")] for line in out]

    return dict(zip(cols, list(map(list, zip(*formatted)))))


def active_from_xyz(
    mesh: DrapeModel | Octree,
    topo: np.ndarray,
    grid_reference="center",
    method="linear",
):
    """Returns an active cell index array below a surface

    :param mesh: Mesh object
    :param topo: Array of xyz locations
    :param grid_reference: Cell reference. Must be "center", "top", or "bottom"
    :param method: Interpolation method. Must be "linear", or "nearest"
    """
    locations = mesh.centroids.copy()

    if method == "linear":
        delaunay_2d = Delaunay(topo[:, :-1])
        z_interpolate = LinearNDInterpolator(delaunay_2d, topo[:, -1])
    elif method == "nearest":
        z_interpolate = NearestNDInterpolator(topo[:, :-1], topo[:, -1])
    else:
        raise ValueError("Method must be 'linear', or 'nearest'")

    if isinstance(mesh, DrapeModel):
        z_offset = cell_size_z(mesh) / 2.0
    else:
        if mesh.w_cell_size is None or mesh.octree_cells is None:
            raise ValueError("Octree mesh must have a cell size")

        z_offset = mesh.octree_cells["NCells"] * np.abs(mesh.w_cell_size) / 2

    # Shift cell center location to top or bottom of cell
    if grid_reference == "top":
        locations[:, -1] += z_offset
    elif grid_reference == "bottom":
        locations[:, -1] -= z_offset
    elif grid_reference == "center":
        pass
    else:
        raise ValueError("'grid_reference' must be one of 'center', 'top', or 'bottom'")

    z_locations = z_interpolate(locations[:, :2])

    # Apply nearest neighbour if in extrapolation
    ind_nan = np.isnan(z_locations)
    if any(ind_nan):
        tree = cKDTree(topo)
        _, ind = tree.query(locations[ind_nan, :])
        z_locations[ind_nan] = topo[ind, -1]

    # fill_nan(locations, z_locations, filler=topo[:, -1])

    # Return the active cell array
    return locations[:, -1] < z_locations
