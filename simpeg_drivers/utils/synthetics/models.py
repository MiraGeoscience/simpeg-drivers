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
from geoapps_utils.modelling.plates import make_plate
from geoh5py.data import FloatData
from geoh5py.objects import DrapeModel, Octree

from simpeg_drivers.utils.synthetics.options import ModelOptions


def get_model(
    method: str,
    mesh: Octree | DrapeModel,
    active: np.ndarray,
    options: ModelOptions,
) -> FloatData:
    """
    Create a halfspace and plate model in the cell centers of the provided mesh.

    :param method: The geophysical method controlling the factory behaviour
    :param mesh: The mesh whose cell centers the model will be defined on.
    :param plate: The plate object defining the location and orientation of the
        plate anomaly.
    :param background: Value given to the halfspace.
    :param anomaly: Value given to the plate.
    """

    cell_centers = mesh.centroids.copy()

    model = make_plate(
        points=cell_centers,
        plate=options.plate,
        background=options.background,
        anomaly=options.anomaly,
    )

    if "1d" in method:
        model = options.background * np.ones(mesh.n_cells)
        inside_anomaly = (mesh.centroids[:, 2] < 0) & (mesh.centroids[:, 2] > -20)
        model[inside_anomaly] = options.anomaly

    model[~active] = np.nan
    model = mesh.add_data({options.name: {"values": model}})
    assert isinstance(model, FloatData)
    return model
