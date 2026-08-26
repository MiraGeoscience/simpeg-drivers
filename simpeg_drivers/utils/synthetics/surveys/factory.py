# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from collections.abc import Callable

import numpy as np
from geoapps_utils.utils.transformations import rotate_xyz
from geoh5py import Workspace
from geoh5py.objects import ObjectBase, Points

from simpeg_drivers.utils.synthetics.options import SurveyOptions

from .dcip import generate_dc_survey
from .frequency_domain.fdem import generate_fdem_survey
from .natural_sources.apparent_conductivity import generate_apparent_conductivity_survey
from .natural_sources.magnetotellurics import generate_magnetotellurics_survey
from .natural_sources.tipper import generate_tipper_survey
from .time_domain.airborne import generate_airborne_tdem_survey
from .time_domain.borehole import generate_borehole_tdem_survey
from .time_domain.ground import generate_tdem_survey


def grid_layout(
    limits: list[float],
    n_stations: int,
    n_lines: int,
    topography: Callable,
    center: tuple[float, float] = (0.0, 0.0),
    rotation: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates grid locations based on limits and spacing.
    """

    x = np.linspace(limits[0], limits[1], n_stations)
    y = np.linspace(limits[2], limits[3], n_lines)
    grid_x, grid_y = np.meshgrid(x, y)

    xy_locs = rotate_xyz(
        np.c_[grid_x.flatten(), grid_y.flatten()], list(center), rotation
    )

    z = topography(xy_locs[:, 0], xy_locs[:, 1])

    return (
        xy_locs[:, 0].reshape(grid_x.shape),
        xy_locs[:, 1].reshape(grid_y.shape),
        z.reshape(grid_x.shape),
    )


def get_survey(
    geoh5: Workspace,
    method: str,
    options: SurveyOptions,
) -> ObjectBase:
    """
    Factory for survey creation with behaviour modified by the provided method.

    :param geoh5: The workspace to create the survey in.
    :param method: The geophysical method controlling the factory behaviour.
    :param options: Survey options.
    """

    grid_x, grid_y, grid_z = grid_layout(
        limits=options.limits,
        n_stations=options.n_stations,
        n_lines=options.n_lines,
        topography=options.topography,
        center=options.center,
        rotation=options.rotation,
    )
    grid_z += options.drape

    if "current" in method or "polarization" in method:
        return generate_dc_survey(geoh5, grid_x, grid_y, grid_z, name=options.name)

    if "magnetotellurics" in method:
        return generate_magnetotellurics_survey(
            geoh5, grid_x, grid_y, grid_z, name=options.name
        )

    if "tipper" in method:
        return generate_tipper_survey(geoh5, grid_x, grid_y, grid_z, name=options.name)

    if "apparent conductivity" in method:
        return generate_apparent_conductivity_survey(
            geoh5, grid_x, grid_y, grid_z, name=options.name
        )

    if method in ["fdem", "fem", "fdem 1d"]:
        return generate_fdem_survey(geoh5, grid_x, grid_y, grid_z, name=options.name)

    if "tdem" in method:
        if "airborne" in method:
            return generate_airborne_tdem_survey(
                geoh5, grid_x, grid_y, grid_z, name=options.name
            )
        elif "borehole" in method:
            return generate_borehole_tdem_survey(
                geoh5, grid_x, grid_y, grid_z, name=options.name
            )

        return generate_tdem_survey(geoh5, grid_x, grid_y, grid_z, name=options.name)

    return Points.create(
        geoh5,
        vertices=np.column_stack(
            [grid_x.flatten(), grid_y.flatten(), grid_z.flatten()]
        ),
        name=options.name,
    )
