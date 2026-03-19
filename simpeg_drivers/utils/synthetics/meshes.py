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
from discretize import TreeMesh
from discretize.utils import mesh_builder_xyz
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.objects import DrapeModel, Octree, Points, Surface
from grid_apps.octree_creation.driver import OctreeDriver
from grid_apps.utils import treemesh_2_octree

from simpeg_drivers.electricals.base_2d import create_mesh_by_line_id
from simpeg_drivers.options import DrapeModelOptions
from simpeg_drivers.plate_simulation.models.options import PlateOptions
from simpeg_drivers.plate_simulation.models.parametric import Plate
from simpeg_drivers.utils.synthetics.options import MeshOptions


def get_mesh(
    method: str,
    survey: Points,
    topography: Surface,
    options: MeshOptions | DrapeModelOptions,
    plate: PlateModel | None = None,
) -> DrapeModel | Octree:
    """Factory for mesh creation with behaviour modified by the provided method."""

    if "2d" in method:
        line_data = survey.get_entity("line_ids")[0]

        return create_mesh_by_line_id(
            survey.workspace,
            survey,
            line_data.values,
            options,
            name="mesh",
        )

    return get_octree_mesh(
        survey=survey,
        topography=topography,
        cell_size=options.cell_size,
        refinement=options.refinement,
        padding_distance=options.padding_distance,
        plate=plate,
        name=options.name,
    )


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
    mesh = OctreeDriver.refine_tree_from_triangulation(
        mesh, topography, levels=refinement, finalize=False
    )

    return mesh


def get_octree_mesh(
    survey: Points,
    topography: Surface,
    cell_size: tuple[float, float, float],
    refinement: tuple | list,
    padding_distance: float,
    plate: PlateModel | None = None,
    name: str = "mesh",
) -> Octree:
    """Generate a survey centered mesh with topography and survey refinement.

    :param survey: Survey object with vertices that define the core of the
        tensor mesh and the source refinement for EM methods.
    :param topography: Surface used to refine the topography.
    :param cell_size: Tuple defining the cell size in all directions.
    :param refinement: Tuple containing the number of cells to refine at each
        level around the topography.
    :param padding_distance: Distance to pad the mesh in all directions.
    :param plate: Optional PlateModel object to refine the mesh around the plate.
    :param name: Name of the Octree object to create in geoh5. Default is "mesh".

    :return entity: The geoh5py Octree object to store the results of
        computation in the shared cells of the computational mesh.
    """

    mesh = get_base_octree(survey, topography, cell_size, (0, 0, 1), padding_distance)

    mesh = OctreeDriver.refine_tree_from_points(
        mesh, survey.vertices, levels=refinement, finalize=False
    )

    if plate is not None:
        # TODO Consolidate PlateOptions and PlateModel into a single class to avoid this redundancy
        plate_options = PlateOptions(
            plate=1.0,  # thickness
            width=plate.width,
            strike_length=plate.strike_length,
            dip_length=plate.dip_length,
            dip=plate.dip,
            dip_direction=plate.direction,
            elevation=0,
        )
        center = list(plate.origin)
        center[2] += plate.width  # Unclear why offsetted vertically
        plate = Plate(plate_options, center=center, workspace=survey.workspace)
        mesh = OctreeDriver.refine_tree_from_triangulation(
            mesh, plate.surface, levels=(4,), finalize=False
        )

    mesh.finalize()
    entity = treemesh_2_octree(survey.workspace, mesh, name=name)

    return entity
