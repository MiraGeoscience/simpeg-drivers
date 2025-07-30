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
from geoh5py.objects import DrapeModel, ObjectBase, Octree, Surface

from .octrees import get_active_source_octree, get_passive_source_octree
from .tensors import get_tensor_mesh


def get_mesh(
    inversion_type: str,
    survey: ObjectBase,
    topography: Surface,
    cell_size: tuple[float, float, float],
    refinement: tuple,
    padding_distance: float,
) -> tuple[DrapeModel | Octree, TensorMesh | TreeMesh]:
    """Factory for mesh creation with behaviour modified by the inversion type."""

    if "2d" in inversion_type:
        return get_tensor_mesh(
            survey,
            cell_size,
            padding_distance,
        )

    if inversion_type in ["fdem", "airborne tdem"]:
        return get_active_source_octree(
            survey, topography, cell_size, refinement, padding_distance
        )

    return get_passive_source_octree(
        survey, topography, cell_size, refinement, padding_distance
    )
