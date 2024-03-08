#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.
#

from __future__ import annotations

import numpy as np
from discretize import TensorMesh, TreeMesh

from simpeg_drivers.components import InversionData


def get_containing_cells(
    mesh: TreeMesh | TensorMesh, data: InversionData
) -> np.ndarray:
    """
    Find indices of cells that contain data locations

    :param mesh: Computational mesh object
    :param data: Inversion data object
    """
    if isinstance(mesh, TreeMesh):
        inds = mesh._get_containing_cell_indexes(  # pylint: disable=protected-access
            data.locations
        )

    elif isinstance(mesh, TensorMesh):
        locations = data.drape_locations(np.unique(data.locations, axis=0))
        xi = np.searchsorted(mesh.nodes_x, locations[:, 0]) - 1
        yi = np.searchsorted(mesh.nodes_y, locations[:, -1]) - 1
        inds = xi * mesh.shape_cells[1] + yi

    else:
        raise TypeError("Mesh must be 'TreeMesh' or 'TensorMesh'")

    return inds
