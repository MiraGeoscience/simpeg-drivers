#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.
#
import numpy as np
from discretize import TensorMesh, TreeMesh

from simpeg_drivers.components import InversionData
from simpeg_drivers.utils.surveys import get_unique_locations


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
        locations = data.drape_locations(get_unique_locations(data.survey))
        xi = np.searchsorted(mesh.nodes_x, locations[:, 0]) - 1
        yi = np.searchsorted(mesh.nodes_y, locations[:, -1]) - 1
        inds = xi + yi * mesh.shape_cells[0]

    else:
        raise TypeError("Mesh must be 'TreeMesh' or 'TensorMesh'")

    return inds
