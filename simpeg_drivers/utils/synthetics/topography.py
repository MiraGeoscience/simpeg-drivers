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
from geoh5py import Workspace
from geoh5py.objects import DrapeModel, Octree, Surface
from scipy.spatial import Delaunay

from simpeg_drivers.utils.synthetics.options import SurveyOptions
from simpeg_drivers.utils.synthetics.surveys.factory import grid_layout
from simpeg_drivers.utils.utils import active_from_xyz


def get_topography_surface(geoh5: Workspace, options: SurveyOptions) -> Surface:
    """
    Returns a topography surface with 2x the limits of the survey.

    :param geoh5: Geoh5 workspace.
    :param options: Survey options. Extents will be 2x the survey extents.
    """

    X, Y, Z = grid_layout(
        limits=[2 * k for k in options.limits],  # type: ignore
        station_spacing=int(np.ceil((options.limits[1] - options.limits[0]) / 4)),
        line_spacing=int(np.ceil((options.limits[3] - options.limits[2]) / 4)),
        topography=options.topography,
    )

    vertices = np.column_stack(
        [X.flatten(order="F"), Y.flatten(order="F"), Z.flatten(order="F")]
    )

    return Surface.create(
        geoh5,
        vertices=vertices,
        cells=Delaunay(vertices[:, :2]).simplices,  # pylint: disable=no-member
        name="topography",
    )


def get_active(
    mesh: Octree | DrapeModel, topography: Surface, name: str = "active_cells"
):
    active = active_from_xyz(mesh, topography.vertices, grid_reference="top")
    return mesh.add_data({name: {"values": active}})
