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
from geoapps_utils.utils.locations import gaussian, mask_large_connections
from geoapps_utils.utils.transformations import y_rotation_matrix
from geoh5py import Workspace
from geoh5py.objects import (
    AirborneTEMReceivers,
    AirborneTEMTransmitters,
    LargeLoopGroundTEMReceivers,
    LargeLoopGroundTEMTransmitters,
)


CHANNELS = np.r_[3e-04, 6e-04, 1.2e-03] * 1e3
WAVEFORM = np.c_[
    np.r_[
        np.arange(-0.002, -0.0001, 5e-4),
        np.arange(-0.0004, 0.0, 1e-4),
        np.arange(0.0, 0.002, 5e-4),
    ]
    * 1e3
    + 2.0,
    np.r_[np.linspace(0, 1, 4), np.linspace(0.9, 0.0, 4), np.zeros(4)],
]


def generate_airborne_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: np.ndarray = CHANNELS,
    waveform: np.ndarray = WAVEFORM,
    name: str = "survey",
) -> AirborneTEMReceivers:
    """Create an Airborne TDEM survey object from survey grid locations"""
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    survey = AirborneTEMReceivers.create(geoh5, vertices=vertices, name=name)
    transmitters = AirborneTEMTransmitters.create(
        geoh5, vertices=vertices, name=f"{name}_tx"
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


def generate_borehole_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: np.ndarray = CHANNELS,
    waveform: np.ndarray = WAVEFORM,
    name: str = "survey",
) -> LargeLoopGroundTEMReceivers:
    """Create a large loop TDEM survey object from survey grid locations."""

    survey = generate_large_loop_survey(
        geoh5, X, Y, Z, channels=channels, waveform=waveform, name=name, n_loops=1
    )

    center = survey.vertices[0, :]
    survey.vertices = (
        y_rotation_matrix(np.pi / 4) @ (survey.vertices - center).T
    ).T + center

    return survey


def generate_galvanic_tdem_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: np.ndarray = CHANNELS,
    waveform: np.ndarray = WAVEFORM,
    name: str = "survey",
):
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    tx_vertices = np.vstack(
        [
            [X.min(), 0, 5],
            [X.max(), 0, 5],
            [0, Y.min(), 5],
            [0, Y.max(), 5],
        ]
    )

    transmitters = LargeLoopGroundTEMTransmitters.create(
        geoh5,
        vertices=tx_vertices,
        cells=np.vstack([[0, 1], [2, 3]]),
        name=f"{name}_tx",
    )
    transmitters.tx_id_property = transmitters.parts + 1

    cells = []
    count = 0
    for _ in range(X.shape[0]):
        inds = np.arange(count, count + X.shape[1] - 1)
        cells.append(np.c_[inds, inds + 1])
        count += X.shape[1]

    survey = LargeLoopGroundTEMReceivers.create(
        geoh5, name=name, vertices=vertices, cells=np.vstack(cells)
    )
    survey.transmitters = transmitters
    blocks = np.array_split(np.arange(vertices.shape[0]).reshape(X.shape), 2, axis=0)
    tx_ids = np.ones(vertices.shape[0])
    for ind, block in enumerate(blocks):
        tx_ids[block.flatten()] = ind + 1
    survey.tx_id_property = tx_ids

    survey.channels = channels

    survey.waveform = waveform
    survey.timing_mark = 2.0
    survey.unit = "Milliseconds (ms)"

    return survey


def generate_large_loop_survey(
    geoh5: Workspace,
    X: np.ndarray,
    Y: np.ndarray,
    Z: np.ndarray,
    channels: np.ndarray = CHANNELS,
    waveform: np.ndarray = WAVEFORM,
    name: str = "survey",
    n_loops: int = 2,
) -> LargeLoopGroundTEMReceivers:
    """Create a large loop TDEM survey object from survey grid locations."""

    flatten = len(np.unique(Z)) == 1
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    center = np.mean(vertices, axis=0)
    if flatten:
        center[2] -= np.mean(Z)

    x_blocks = np.array_split(X, n_loops, axis=0)
    y_blocks = np.array_split(Y, n_loops, axis=0)
    z_blocks = np.array_split(Z, n_loops, axis=0)
    arrays = [
        np.c_[x.flatten(), y.flatten(), z.flatten()]
        for x, y, z in zip(x_blocks, y_blocks, z_blocks, strict=True)
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
        loops += [np.c_[loop, elevation]]
        loop_cells += [np.c_[np.arange(15) + count, np.arange(15) + count + 1]]
        loop_cells += [np.c_[count + 15, count]]
        count += 16

    transmitters = LargeLoopGroundTEMTransmitters.create(
        geoh5,
        vertices=np.vstack(loops),
        cells=np.vstack(loop_cells),
        name=f"{name}_tx",
    )
    transmitters.tx_id_property = transmitters.parts + 1

    cells = []
    count = 0
    for _ in range(X.shape[0]):
        inds = np.arange(count, count + X.shape[1] - 1)
        cells.append(np.c_[inds, inds + 1])
        count += X.shape[1]

    survey = LargeLoopGroundTEMReceivers.create(
        geoh5, name=name, vertices=vertices, cells=np.vstack(cells)
    )
    survey.transmitters = transmitters
    survey.tx_id_property = np.hstack(loop_id)

    survey.channels = channels

    survey.waveform = waveform
    survey.timing_mark = 2.0
    survey.unit = "Milliseconds (ms)"

    return survey
