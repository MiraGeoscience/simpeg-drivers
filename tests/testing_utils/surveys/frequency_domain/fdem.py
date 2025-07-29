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
from geoh5py.objects import AirborneFEMReceivers, AirborneFEMTransmitters

from . import frequency_config


def generate_fdem_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
):
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    survey = AirborneFEMReceivers.create(geoh5, vertices=vertices, name="Airborne_rx")

    survey.metadata["EM Dataset"]["Frequency configurations"] = frequency_config

    tx_locs = []
    freqs = []
    for config in frequency_config:
        tx_vertices = vertices.copy()
        tx_vertices[:, 0] -= config["Offset"]
        tx_locs.append(tx_vertices)
        freqs.append([[config["Frequency"]] * len(vertices)])
    tx_locs = np.vstack(tx_locs)
    freqs = np.hstack(freqs).flatten()

    transmitters = AirborneFEMTransmitters.create(
        geoh5, vertices=tx_locs, name="Airborne_tx"
    )
    survey.transmitters = transmitters
    survey.channels = [k["Frequency"] for k in frequency_config]

    transmitters.add_data(
        {
            "Tx frequency": {
                "values": freqs,
                "association": "VERTEX",
                "primitive_type": "REFERENCED",
                "value_map": {k: str(k) for k in freqs},
            }
        }
    )

    survey.remove_cells(mask_large_connections(survey, 200.0))
    transmitters.remove_cells(mask_large_connections(transmitters, 200.0))

    return survey
