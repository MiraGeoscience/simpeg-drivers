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
from geoh5py import Workspace
from geoh5py.objects import CurrentElectrode, PotentialElectrode


def generate_dc_survey(
    workspace: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray | None = None,
    name: str = "survey",
) -> PotentialElectrode:
    """Generate a DC survey object from survey grid locations."""

    if Z is None:
        Z = np.zeros_like(X)

    vertices = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
    parts = np.kron(np.arange(X.shape[0]), np.ones(X.shape[1])).astype("int")
    currents = CurrentElectrode.create(
        workspace, name=f"{name}_tx", vertices=vertices, parts=parts
    )
    currents.add_default_ab_cell_id()
    n_dipoles = 9
    dipoles = []
    current_id = []

    for val in currents.ab_cell_id.values:
        cell_id = int(currents.ab_map[val]) - 1

        for dipole in range(n_dipoles):
            dipole_ids = currents.cells[cell_id, :] + 2 + dipole

            if (
                any(dipole_ids > (currents.n_vertices - 1))
                or len(
                    np.unique(parts[np.r_[currents.cells[cell_id, 0], dipole_ids[1]]])
                )
                > 1
            ):
                continue

            dipoles += [dipole_ids]
            current_id += [val]

    potentials = PotentialElectrode.create(
        workspace,
        name=name,
        vertices=vertices,
        cells=np.vstack(dipoles).astype("uint32"),
    )
    line_id = potentials.vertices[potentials.cells[:, 0], 1]
    line_id = (line_id - np.min(line_id) + 1).astype(np.int32)
    line_reference = {0: "Unknown"}
    line_reference.update({k: str(k) for k in np.unique(line_id)})
    potentials.add_data(
        {
            "line_ids": {
                "values": line_id,
                "type": "REFERENCED",
                "value_map": line_reference,
            }
        }
    )
    potentials.ab_cell_id = np.hstack(current_id).astype("int32")
    potentials.current_electrodes = currents
    currents.potential_electrodes = potentials

    return potentials
