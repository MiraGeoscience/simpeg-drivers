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
from geoh5py.objects import Points

from tests.testing_utils.surveys import (
    generate_airborne_tdem_survey,
    generate_dc_survey,
    generate_fdem_survey,
    generate_magnetotellurics_survey,
    generate_tdem_survey,
    generate_tipper_survey,
)


def get_survey(
    geoh5: Workspace,
    inversion_type: str,
    limits: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    station_spacing,
    line_spacing,
    topography: Callable | float,
    drape_height: float,
):
    X, Y, Z = grid_layout(
        limits=limits,
        station_spacing=station_spacing,
        line_spacing=line_spacing,
        topography=topography,
    )
    Z += drape_height

    if "current" in inversion_type or "polarization" in inversion_type:
        return generate_dc_survey(geoh5, X, Y, Z)

    if "magnetotellurics" in inversion_type:
        return generate_magnetotellurics_survey(geoh5, X, Y, Z)

    if "tipper" in inversion_type:
        return generate_tipper_survey(geoh5, X, Y, Z)

    if inversion_type in ["fdem", "fem", "fdem 1d"]:
        return generate_fdem_survey(geoh5, X, Y, Z)

    if "airborne tdem" in inversion_type:
        return generate_airborne_tdem_survey(geoh5, X, Y, Z)

    if "ground tdem" in inversion_type:
        return generate_tdem_survey(geoh5, X, Y, Z)

    return Points.create(
        geoh5,
        vertices=np.column_stack([X.flatten(), Y.flatten(), Z.flatten()]),
        name="survey",
    )
