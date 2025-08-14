# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of geoapps-utils package.                                      '
#                                                                                   '
#  geoapps-utils is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.utils.locations import mask_large_connections
from geoh5py import Workspace
from geoh5py.objects import (
    AirborneTEMReceivers,
    AirborneTEMTransmitters,
)

from simpeg_drivers.utils.synthetics.surveys.time_domain import channels, waveform


def generate_airborne_tdem_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
) -> AirborneTEMReceivers:
    """Create an Airborne TDEM survey object from survey grid locations"""
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    survey = AirborneTEMReceivers.create(geoh5, vertices=vertices, name="Airborne_rx")
    transmitters = AirborneTEMTransmitters.create(
        geoh5, vertices=vertices, name="Airborne_tx"
    )
    mask = mask_large_connections(survey, 200.0)
    survey.remove_cells(mask)
    transmitters.remove_cells(mask)

    survey.transmitters = transmitters
    survey.channels = channels
    survey.waveform = waveform
    survey.timing_mark = 2.0
    survey.unit = "Milliseconds (ms)"

    return survey
