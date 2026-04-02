# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np

from simpeg_drivers.utils.utils import mask_vertices_and_cells


def test_mask_vertices_and_cells():
    X, Y = np.meshgrid(np.arange(3), np.arange(3))
    Z = np.zeros_like(X)
    vertices = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    cells = np.array(
        [
            [0, 1, 3],
            [3, 1, 4],
            [1, 2, 4],
            [4, 2, 5],
            [3, 4, 6],
            [6, 4, 7],
            [4, 5, 7],
            [7, 5, 8],
        ]
    )
    extent = np.vstack([[0.5, 0, 0], [2, 2, 1]])
    masked_vertices, masked_cells = mask_vertices_and_cells(extent, vertices, cells)
    assert len(masked_vertices) == len(vertices)
    assert len(masked_cells) == len(cells)
    extent = np.vstack([[1.5, 0, 0], [2, 2, 1]])
    masked_vertices, masked_cells = mask_vertices_and_cells(extent, vertices, cells)
    assert len(masked_vertices) == 6
    assert len(masked_cells) == 4
