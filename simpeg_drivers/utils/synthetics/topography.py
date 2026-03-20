# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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

from simpeg_drivers.options import DrapeModelOptions
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from simpeg_drivers.utils.synthetics.surveys.factory import grid_layout
from simpeg_drivers.utils.utils import active_from_xyz


def get_topography_surface(
    geoh5: Workspace, options: SyntheticsComponentsOptions
) -> Surface:
    """
    Returns topography with same limits as the mesh and 2x resolution of the survey.

    :param geoh5: Geoh5 workspace.
    :param options: Options containing survey and mesh specifications.
    """

    width, height = compute_mesh_extents(options.survey, options.mesh)
    X, Y, Z = grid_layout(
        limits=[
            options.survey.center[0] - width / 2,
            options.survey.center[0] + width / 2,
            options.survey.center[1] - height / 2,
            options.survey.center[1] + height / 2,
        ],
        n_stations=64,
        n_lines=64,
        topography=options.survey.topography,
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


def compute_mesh_extents(
    survey_options: SurveyOptions, mesh_options: MeshOptions | DrapeModelOptions
) -> tuple[float, float]:
    """
    Estimates the extent of the mesh from survey and mesh options.

    :param survey_options: Survey options.
    :param mesh_options: Mesh options.

    :return: mesh width including padding.
    :return: mesh height including padding.
    """
    width = survey_options.width
    height = survey_options.height

    if isinstance(mesh_options, DrapeModelOptions):
        cell_size = (mesh_options.u_cell_size, mesh_options.u_cell_size)
        padding = mesh_options.horizontal_padding
    else:
        cell_size = mesh_options.cell_size
        padding = mesh_options.padding_distance

    def next_pow2_cells(span, cell_size, padding):
        return 2 ** np.ceil(np.log2((span + 2 * padding) / cell_size))

    return (
        cell_size[0] * next_pow2_cells(width, cell_size[0], padding),
        cell_size[1] * next_pow2_cells(height, cell_size[1], padding),
    )


def get_active(
    mesh: Octree | DrapeModel, topography: Surface, name: str = "active_cells"
):
    active = active_from_xyz(
        mesh, topography.vertices, grid_reference="top", triangulation=topography.cells
    )
    return mesh.add_data({name: {"values": active}})
