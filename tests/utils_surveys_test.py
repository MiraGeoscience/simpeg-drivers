# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part simpeg-drivers package.                                        '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import numpy as np

from simpeg_drivers.utils.surveys import counter_clockwise_sort


def test_counterclockwise_sort():
    vertices = np.array(
        [[0, 0], [0.25, 1.5], [0.0, 2.0], [0.5, 1], [1.5, 0], [0.2, 0.2]]
    )
    segments = np.c_[np.arange(len(vertices)), np.arange(1, len(vertices) + 1)]
    segments[-1, 1] = 0

    ccw_sorted = counter_clockwise_sort(segments, vertices)

    np.testing.assert_equal(ccw_sorted[0, :], [0, 5])
