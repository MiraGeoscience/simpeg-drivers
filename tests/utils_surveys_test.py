# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import numpy as np

from simpeg_drivers.utils.surveys import counter_clockwise_sort


def test_counterclockwise_sort():
    segments = np.array([[0, 3], [3, 2], [2, 1], [1, 0]])
    vertices = np.array([[0, 0], [1.5, 0], [0.5, 1], [0.1, 1.5]])

    ccw_sorted = counter_clockwise_sort(segments, vertices)

    np.testing.assert_equal(ccw_sorted[0, :], [0, 1])
