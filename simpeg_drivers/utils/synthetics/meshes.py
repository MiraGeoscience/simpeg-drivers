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
from geoh5py.objects import DrapeModel, Octree, Points, Surface
from grid_apps.octree_creation.driver import OctreeDriver

from simpeg_drivers.electricals.base_2d import create_mesh_by_line_id
from simpeg_drivers.options import DrapeModelOptions
from simpeg_drivers.utils.synthetics.options import MeshOptions


def get_mesh(
    method: str,
    survey: Points,
    topography: Surface,
    options: MeshOptions | DrapeModelOptions,
    plates: list[Surface] | None = None,
) -> DrapeModel | Octree:
    """
    Factory for mesh creation with behaviour modified by the provided method.

    :param method: Geophysical method dictating if Octree (3d) or DrapeModel
        (2d) mesh is returned.
    :param survey: Survey object for point refinement.
    :param topography: Topography object for surface refinement.
    :param options: Mesh creation options specifying core and refinement options.
    :param plates: Optional plate surfaces to refine.

    :return: A DrapeModel for 2D methods, or an Octree for all other methods.
    """

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
        options,
        survey=survey,
        topography=topography,
        plates=plates,
        name=options.name,
    )


def get_octree_mesh(
    opts: MeshOptions,
    survey: Points,
    topography: Surface,
    plates: list[Surface] | None = None,
    name: str = "octree",
) -> Octree:
    """Generate a survey centered mesh with topography and survey refinement.

    :param opts: Octree mesh creation options.
    :param survey: Survey object with vertices that define the core of the
        tensor mesh and the source refinement for EM methods.
    :param topography: Surface used to refine the topography.
    :param plates: Optional plate surfaces to refine.
    :param name: Name of the Octree object to create in geoh5.

    :return mesh: The geoh5py Octree object to store the results of
        computation in the shared cells of the computational mesh.
    """
    octree_params = opts.octree_params(survey, topography, plates)
    octree_driver = OctreeDriver(octree_params)
    mesh = octree_driver.run()
    mesh.name = name
    return mesh
