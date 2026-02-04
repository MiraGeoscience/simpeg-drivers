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
from geoapps_utils.utils.locations import mask_large_connections
from geoh5py import Workspace
from geoh5py.objects.surveys.electromagnetics.airborne_app_con import (
    AirborneAppConBaseStations,
    AirborneAppConReceivers,
)


def generate_apparent_conductivity_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: tuple = (10.0, 50.0, 200.0),
    name: str = "survey",
) -> AirborneAppConReceivers:
    """Create a Tipper survey object from survey grid locations."""
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    survey = AirborneAppConReceivers.create(
        geoh5,
        vertices=vertices,
        name=name,
        channels=list(channels),
    )
    base_station = AirborneAppConBaseStations.create(
        geoh5, vertices=np.c_[-100, -100, -0.0]
    )
    base_station.tx_id_property = np.r_[1]

    survey.base_stations = base_station
    survey.tx_id_property = np.ones(survey.n_vertices, dtype=int)
    survey.remove_cells(mask_large_connections(survey, 200.0))

    return survey
