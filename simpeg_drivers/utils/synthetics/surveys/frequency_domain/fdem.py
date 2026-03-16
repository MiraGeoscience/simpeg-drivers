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
from geoh5py.objects import AirborneFEMReceivers, AirborneFEMTransmitters


frequency_config = [
    {"Coaxial data": False, "Frequency": 900, "Offset": 7.86},
    {"Coaxial data": False, "Frequency": 7200, "Offset": 7.86},
    {"Coaxial data": False, "Frequency": 56000, "Offset": 6.3},
]


def generate_fdem_survey(
    geoh5: Workspace,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    z_grid: np.ndarray,
    name: str = "survey",
) -> AirborneFEMReceivers:
    """Create an FDEM survey object from survey grid locations."""

    vertices = np.column_stack([x_grid.flatten(), y_grid.flatten(), z_grid.flatten()])

    if len(vertices) < 2:
        raise ValueError("FDEM survey requires at least 2 vertices")

    survey = AirborneFEMReceivers.create(geoh5, vertices=vertices, name=name)
    survey.remove_cells(mask_large_connections(survey, 200.0))
    survey.metadata["EM Dataset"]["Frequency configurations"] = frequency_config

    tx_locs_list = []
    frequency_list = []

    for config in frequency_config:
        for part in np.unique(survey.parts):
            line = survey.parts == part
            delta = np.diff(vertices[line, :], axis=0)
            length = np.linalg.norm(delta, axis=1)

            if np.any(length <= 0):
                raise ValueError("FDEM should not have duplicate vertices")

            delta /= length[:, None]
            delta = np.vstack([delta, delta[-1, :]])  # Repeat last offset

            tx_vertices = vertices[line, :] - delta * config["Offset"]
            tx_locs_list.append(tx_vertices)
            frequency_list.append([[config["Frequency"]] * sum(line)])

    tx_locs = np.vstack(tx_locs_list)
    freqs = np.hstack(frequency_list).flatten()

    transmitters = AirborneFEMTransmitters.create(
        geoh5, vertices=tx_locs, name=f"{name}_tx"
    )
    survey.transmitters = transmitters
    survey.channels = [float(k["Frequency"]) for k in frequency_config]

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

    transmitters.remove_cells(mask_large_connections(transmitters, 200.0))

    return survey
