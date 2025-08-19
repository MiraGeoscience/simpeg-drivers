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
from geoapps_utils.utils.locations import mask_large_connections
from geoh5py import Workspace
from geoh5py.objects.surveys.electromagnetics.tipper import (
    TipperBaseStations,
    TipperReceivers,
)


def generate_tipper_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: tuple = (10.0, 100.0, 1000.0),
    name: str = "survey",
) -> TipperReceivers:
    """Create a Tipper survey object from survey grid locations."""
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    survey = TipperReceivers.create(
        geoh5,
        vertices=vertices,
        name=name,
        components=[
            "Txz (real)",
            "Txz (imag)",
            "Tyz (real)",
            "Tyz (imag)",
        ],
        channels=list(channels),
    )
    survey.base_stations = TipperBaseStations.create(
        geoh5, vertices=np.c_[vertices[0, :]].T
    )
    survey.remove_cells(mask_large_connections(survey, 200.0))

    return survey
