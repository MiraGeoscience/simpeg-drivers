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
from geoh5py.data import IntegerData
from geoh5py.objects import CellObject, DrapeModel

from simpeg_drivers.utils.utils import get_drape_model


def get_tensor_mesh(
    survey: CellObject,
    cell_size: tuple[float, float, float],
    padding_distance: float,
    line_id: int = 101,
    name: str = "mesh",
) -> DrapeModel:
    """
    Generate a tensor mesh and the colocated DrapeModel.

    :param survey: Survey object with vertices that define the core of the
        tensor mesh.
    :param cell_size: Tuple defining the cell size in all directions.
    :param padding_distance: Distance to pad the mesh in all directions.
    :param line_id: Chooses line from the survey to define the drape model.

    :return entity: The DrapeModel object that shares cells with the discretize
        tensor mesh and which stores the results of computations.
    :return mesh: The discretize tensor mesh object for computations.
    """

    line_data = survey.get_entity("line_ids")[0]
    assert isinstance(line_data, IntegerData)
    lines = line_data.values
    entity, _mesh, _ = get_drape_model(  # pylint: disable=unbalanced-tuple-unpacking
        survey.workspace,
        name,
        survey.vertices[np.unique(survey.cells[lines == line_id, :]), :],
        [cell_size[0], cell_size[2]],
        100.0,
        [padding_distance] * 2 + [padding_distance] * 2,
        1.1,
        parent=None,
        return_colocated_mesh=True,
        return_sorting=True,
    )

    return entity
