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
from geoh5py import Workspace
from geoh5py.objects import ObjectBase, Points

from simpeg_drivers.utils.testing_utils.options import SurveyOptions
from simpeg_drivers.utils.testing_utils.surveys.layout import grid_layout

from .dcip import generate_dc_survey
from .frequency_domain.fdem import generate_fdem_survey
from .natural_sources.magnetotellurics import generate_magnetotellurics_survey
from .natural_sources.tipper import generate_tipper_survey
from .time_domain.airborne_tdem import generate_airborne_tdem_survey
from .time_domain.ground_tdem import generate_tdem_survey


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

    limits = [
        options.center[0] - options.width / 2,
        options.center[0] + options.width / 2,
        options.center[1] - options.height / 2,
        options.center[1] + options.height / 2,
    ]
    X, Y, Z = grid_layout(
        limits=limits,
        station_spacing=options.n_stations,
        line_spacing=options.n_lines,
        terrain=options.terrain,
    )
    Z += options.drape

    if "current" in method or "polarization" in method:
        return generate_dc_survey(geoh5, X, Y, Z)

    if "magnetotellurics" in method:
        return generate_magnetotellurics_survey(geoh5, X, Y, Z)

    if "tipper" in method:
        return generate_tipper_survey(geoh5, X, Y, Z)

    if method in ["fdem", "fem", "fdem 1d"]:
        return generate_fdem_survey(geoh5, X, Y, Z)

    if "tdem" in method:
        if "airborne" in method:
            return generate_airborne_tdem_survey(geoh5, X, Y, Z)
        else:
            return generate_tdem_survey(geoh5, X, Y, Z)

    return Points.create(
        geoh5,
        vertices=np.column_stack([X.flatten(), Y.flatten(), Z.flatten()]),
        name="survey",
    )
