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
from discretize.utils import mesh_builder_xyz
from geoh5py.objects import Octree, Points, Surface
from grid_apps.octree_creation.driver import OctreeDriver
from grid_apps.utils import treemesh_2_octree


def get_base_octree(
    survey: Points,
    topography: Surface,
    cell_size: tuple[float, float, float],
    refinement: tuple,
    padding: float,
) -> TreeMesh:
    """
    Generate a survey centered TreeMesh object with topography refinement.

    :param survey: Survey object with vertices that define the core of the
        tensor mesh.
    :param topography: Surface used to refine the topography.
    :param cell_size: Tuple defining the cell size in all directions.
    :param refinement: Tuple containing the number of cells to refine at each
        level around the topography.
    :param padding: Distance to pad the mesh in all directions.

    :return mesh: The discretize TreeMesh object for computations.
    """
    padding_distance = np.ones((3, 2)) * padding
    mesh = mesh_builder_xyz(
        survey.vertices - np.r_[cell_size] / 2.0,
        cell_size,
        depth_core=100.0,
        padding_distance=padding_distance,
        mesh_type="TREE",
        tree_diagonal_balance=False,
    )
    mesh = OctreeDriver.refine_tree_from_surface(
        mesh, topography, levels=refinement, finalize=False
    )

    return mesh


def get_octree_mesh(
    survey: Points,
    topography: Surface,
    cell_size: tuple[float, float, float],
    refinement: tuple,
    padding_distance: float,
    refine_on_receivers: bool,
    name: str = "mesh",
) -> Octree:
    """Generate a survey centered mesh with topography and survey refinement.

    :param survey: Survey object with vertices that define the core of the
        tensor mesh and the source refinement for EM methods.
    :param topography: Surface used to refine the topography.
    :param cell_size: Tuple defining the cell size in all directions.
    :param refinement: Tuple containing the number of cells to refine at each
        level around the topography.
    :param padding: Distance to pad the mesh in all directions.
    :param refine_on_receivers: Refine on the survey locations or not.

    :return entity: The geoh5py Octree object to store the results of
        computation in the shared cells of the computational mesh.
    :return mesh: The discretize TreeMesh object for computations.
    """

    mesh = get_base_octree(survey, topography, cell_size, refinement, padding_distance)

    if refine_on_receivers:
        mesh = OctreeDriver.refine_tree_from_points(
            mesh, survey.vertices, levels=[2], finalize=False
        )

    mesh.finalize()
    entity = treemesh_2_octree(survey.workspace, mesh, name=name)

    return entity
