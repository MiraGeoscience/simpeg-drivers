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
from geoapps_utils.utils.transformations import y_rotation_matrix
from geoh5py import Workspace
from geoh5py.objects import (
    LargeLoopGroundTEMReceivers,
)

from simpeg_drivers.utils.synthetics.surveys.time_domain import CHANNELS, WAVEFORM
from simpeg_drivers.utils.synthetics.surveys.time_domain.ground import (
    generate_tdem_survey,
)


def generate_borehole_tdem_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: np.ndarray = CHANNELS,
    waveform: np.ndarray = WAVEFORM,
    name: str = "survey",
) -> LargeLoopGroundTEMReceivers:
    """Create a large loop TDEM survey object from survey grid locations."""

    survey = generate_tdem_survey(
        geoh5, X, Y, Z, channels=channels, waveform=waveform, name=name, n_loops=1
    )

    center = survey.vertices[0, :]
    survey.vertices = (
        y_rotation_matrix(np.pi / 2) @ (survey.vertices - center).T
    ).T + center

    return survey
