# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from plate_simulation.models.parametric import Plate


def azimuth_to_unit_vector(azimuth: float) -> np.ndarray:
    """
    Convert an azimuth to a unit vector.

    :param azimuth: Azimuth in degrees from north (0 to 360).
    :return: Unit vector in the direction of the azimuth.
    """
    theta = np.deg2rad(azimuth)
    mat_z = np.r_[
        np.c_[np.cos(theta), -np.sin(theta), 0.0],
        np.c_[np.sin(theta), np.cos(theta), 0.0],
        np.c_[0.0, 0.0, 1.0],
    ]
    return np.array([0.0, 1.0, 0.0]).dot(mat_z)


def replicate(
    plate: Plate,
    number: int,
    spacing: float,
    azimuth: float,
) -> list[Plate]:
    """
    Replicate a plate n times along an azimuth centered at origin.

    Plate names will be indexed.

    :param plate: models.parametric.Plate to be replicated.
    :param number: Number of plates returned.
    :param spacing: Spacing between plates.
    :param azimuth: Azimuth of the axis along with plates are replicated.
    """

    offsets = (np.arange(number) * spacing) - ((number - 1) * spacing / 2)

    plates = []
    for i in range(number):
        center = np.r_[plate.center] + azimuth_to_unit_vector(azimuth) * offsets[i]
        new = Plate(plate.params.copy(), center)
        new.params.name = f"{plate.params.name} offset {i + 1}"
        plates.append(new)
    return plates
