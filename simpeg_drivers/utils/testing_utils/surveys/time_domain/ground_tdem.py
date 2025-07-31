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
from geoh5py.objects import (
    LargeLoopGroundTEMReceivers,
    LargeLoopGroundTEMTransmitters,
)

from simpeg_drivers.utils.testing_utils.terrain import gaussian


channels = np.r_[3e-04, 6e-04, 1.2e-03] * 1e3
waveform = np.c_[
    np.r_[
        np.arange(-0.002, -0.0001, 5e-4),
        np.arange(-0.0004, 0.0, 1e-4),
        np.arange(0.0, 0.002, 5e-4),
    ]
    * 1e3
    + 2.0,
    np.r_[np.linspace(0, 1, 4), np.linspace(0.9, 0.0, 4), np.zeros(4)],
]


def generate_tdem_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
) -> LargeLoopGroundTEMReceivers:
    """Create a large loop TDEM survey object from survey grid locations."""

    flatten = len(np.unique(Z)) == 1
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    center = np.mean(vertices, axis=0)
    if flatten:
        center[2] -= np.unique(Z)
    n_lines = X.shape[0]
    arrays = [
        np.c_[
            X[: int(n_lines / 2), :].flatten(),
            Y[: int(n_lines / 2), :].flatten(),
            Z[: int(n_lines / 2), :].flatten(),
        ],
        np.c_[
            X[int(n_lines / 2) :, :].flatten(),
            Y[int(n_lines / 2) :, :].flatten(),
            Z[int(n_lines / 2) :, :].flatten(),
        ],
    ]
    loops = []
    loop_cells = []
    loop_id = []
    count = 0
    for ind, array in enumerate(arrays):
        loop_id += [np.ones(array.shape[0]) * (ind + 1)]
        min_loc = np.min(array, axis=0)
        max_loc = np.max(array, axis=0)
        loop = np.vstack(
            [
                np.c_[
                    np.ones(5) * min_loc[0],
                    np.linspace(min_loc[1], max_loc[1], 5),
                ],
                np.c_[
                    np.linspace(min_loc[0], max_loc[0], 5)[1:],
                    np.ones(4) * max_loc[1],
                ],
                np.c_[
                    np.ones(4) * max_loc[0],
                    np.linspace(max_loc[1], min_loc[1], 5)[1:],
                ],
                np.c_[
                    np.linspace(max_loc[0], min_loc[0], 5)[1:-1],
                    np.ones(3) * min_loc[1],
                ],
            ]
        )
        loop = (loop - np.mean(loop, axis=0)) * 1.5 + np.mean(loop, axis=0)
        elevation = (
            np.ones(len(loop)) * np.unique(Z)
            if flatten
            else gaussian(loop[:, 0], loop[:, 1], amplitude=50.0, width=100.0)
        )
        loop = np.c_[loop, elevation]
        loops += [loop + np.asarray(center)]
        loop_cells += [np.c_[np.arange(15) + count, np.arange(15) + count + 1]]
        loop_cells += [np.c_[count + 15, count]]
        count += 16

    transmitters = LargeLoopGroundTEMTransmitters.create(
        geoh5,
        vertices=np.vstack(loops),
        cells=np.vstack(loop_cells),
    )
    transmitters.tx_id_property = transmitters.parts + 1
    survey = LargeLoopGroundTEMReceivers.create(geoh5, vertices=np.vstack(vertices))
    survey.transmitters = transmitters
    survey.tx_id_property = np.hstack(loop_id)

    survey.channels = channels

    survey.waveform = waveform
    survey.timing_mark = 2.0
    survey.unit = "Milliseconds (ms)"

    return survey
