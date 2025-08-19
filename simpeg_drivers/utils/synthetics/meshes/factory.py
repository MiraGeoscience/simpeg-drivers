# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from discretize import TensorMesh, TreeMesh
from geoh5py.objects import CellObject, DrapeModel, Octree, Points, Surface

from simpeg_drivers.utils.synthetics.options import MeshOptions

from .octrees import get_octree_mesh
from .tensors import get_tensor_mesh


def get_mesh(
    method: str,
    survey: Points,
    topography: Surface,
    options: MeshOptions,
) -> DrapeModel | Octree:
    """Factory for mesh creation with behaviour modified by the provided method."""

    if "2d" in method:
        assert isinstance(survey, CellObject)
        return get_tensor_mesh(
            survey=survey,
            cell_size=options.cell_size,
            padding_distance=options.padding_distance,
            name=options.name,
        )

    return get_octree_mesh(
        survey=survey,
        topography=topography,
        cell_size=options.cell_size,
        refinement=options.refinement,
        padding_distance=options.padding_distance,
        refine_on_receivers=method in ["fdem", "airborne tdem"],
        name=options.name,
    )
