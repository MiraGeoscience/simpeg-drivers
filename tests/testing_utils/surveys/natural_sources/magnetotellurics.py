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
from geoh5py import Workspace
from geoh5py.objects.surveys.electromagnetics.magnetotellurics import MTReceivers

from . import channels


def generate_magnetotellurics_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
) -> MTReceivers:
    """Create a Magnetotellurics survey object from survey grid locations."""

    survey = MTReceivers.create(
        geoh5,
        vertices=np.column_stack([X.flatten(), Y.flatten(), Z.flatten()]),
        name="survey",
        components=[
            "Zxx (real)",
            "Zxx (imag)",
            "Zxy (real)",
            "Zxy (imag)",
            "Zyx (real)",
            "Zyx (imag)",
            "Zyy (real)",
            "Zyy (imag)",
        ],
        channels=channels,
    )
    return survey
