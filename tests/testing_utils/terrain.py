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
from geoapps_utils.utils.locations import grid_layout
from geoh5py import Workspace
from geoh5py.objects import Surface
from scipy.spatial import Delaunay


def gaussian(
    x: np.ndarray, y: np.ndarray, amplitude: float, width: float
) -> np.ndarray:
    """
    Gaussian function for 2D data.

    :param x: X-coordinates.
    :param y: Y-coordinates.
    :param amplitude: Amplitude of the Gaussian.
    :param width: Width parameter of the Gaussian.
    """

    return amplitude * np.exp(-0.5 * ((x / width) ** 2.0 + (y / width) ** 2.0))


def get_topography_surface(
    geoh5: Workspace,
    survey_limits: tuple[float, float, float, float],
    topography: Callable | float = 0,
    shift: float = 0,
) -> Surface:
    """
    Returns a topography surface with 2x the limits of the survey.

    :param geoh5: Geoh5 workspace.
    :param survey_limits: Tuple of (xmin, xmax, ymin, ymax) defining the survey limits.
    :param topography: Callable or float defining the topography function.
    :param shift: Static shift to add to the z values.
    """

    X, Y, Z = grid_layout(
        limits=tuple(2 * k for k in survey_limits),
        station_spacing=int(np.ceil((survey_limits[1] - survey_limits[0]) / 4)),
        line_spacing=int(np.ceil((survey_limits[3] - survey_limits[2]) / 4)),
        topography=topography,
    )
    Z += shift

    vertices = np.column_stack(
        [X.flatten(order="F"), Y.flatten(order="F"), Z.flatten(order="F")]
    )

    return Surface.create(
        geoh5,
        vertices=vertices,
        cells=Delaunay(vertices[:, :2]).simplices,  # pylint: disable=no-member
        name="topography",
    )
