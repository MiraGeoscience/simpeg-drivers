# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from collections.abc import Callable

import numpy as np


def grid_layout(
    limits: tuple[float, float, float, float],
    station_spacing: int,
    line_spacing: int,
    terrain: Callable,
):
    """
    Generates grid locations based on limits and spacing.

    :param limits: Tuple of (xmin, xmax, ymin, ymax).
    :param station_spacing: Number of stations along each line.
    :param line_spacing: Number of lines in the grid.
    :param terrain: Callable that generates the terrain (z values).
    """

    x = np.linspace(limits[0], limits[1], station_spacing)
    y = np.linspace(limits[2], limits[3], line_spacing)
    X, Y = np.meshgrid(x, y)
    Z = terrain(X, Y)

    return X, Y, Z
