# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np

from simpeg_drivers.potential_fields import (
    MagneticForwardOptions,
)
from simpeg_drivers.potential_fields.magnetic_scalar.driver import (
    MagneticForwardDriver,
)
from simpeg_drivers.utils.testing_utils.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticDataInversionOptions,
)
from simpeg_drivers.utils.testing_utils.runtests import setup_inversion_workspace


TARGET = 1132.1998


def test_automesh(
    tmp_path: Path,
    n_grid_points=20,
    refinement=(4, 8),
):
    # Run the forward
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="magnetic_scalar", options=opts
    )
    inducing_field = (49999.8, 90.0, 0.0)
    params = MagneticForwardOptions.build(
        forward_only=True,
        geoh5=geoh5,
        mesh=None,
        topography_object=topography,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        data_object=survey,
        starting_model=model,
    )

    fwr_driver = MagneticForwardDriver(params)
    fwr_driver.run()

    with geoh5.open(mode="r"):
        data = geoh5.get_entity("Iteration_0_tmi")[0].values
        assert np.isclose(np.linalg.norm(data), TARGET)
