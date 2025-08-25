# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import numpy as np
from geoh5py import Workspace

from simpeg_drivers.potential_fields import GravityInversionOptions
from simpeg_drivers.potential_fields.gravity.driver import GravityInversionDriver
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import get_workspace


def test_smallness_terms(tmp_path: Path):
    n_grid_points = 2
    refinement = (2,)

    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(n_stations=n_grid_points, n_lines=n_grid_points),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.75),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        gz = components.survey.add_data(
            {"gz": {"values": np.ones(components.survey.n_vertices)}}
        )
        mesh = components.model.parent

        params = GravityInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=components.topography,
            data_object=gz.parent,
            starting_model=1e-4,
            reference_model=0.0,
            alpha_s=1.0,
            s_norm=0.0,
            gz_channel=gz,
            gz_uncertainty=2e-3,
            lower_bound=0.0,
            max_global_iterations=1,
            initial_beta_ratio=1e-2,
            percentile=100,
        )
        params.alpha_s = None
        driver = GravityInversionDriver(params)
        assert driver.regularization.objfcts[0].alpha_s == 1.0


def test_target_chi(tmp_path: Path, caplog):
    n_grid_points = 2
    refinement = (2,)

    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(n_station=n_grid_points, n_lines=n_grid_points),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.75),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        gz = components.survey.add_data(
            {"gz": {"values": np.ones(components.survey.n_vertices)}}
        )
        mesh = components.model.parent
        params = GravityInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=components.topography,
            data_object=gz.parent,
            gz_channel=gz,
            gz_uncertainty=2e-3,
            starting_model=1e-4,
            starting_chi_factor=1.0,
            chi_factor=2.0,
        )
        driver = GravityInversionDriver(params)

        with caplog.at_level("WARNING"):
            assert driver.directives.update_irls_directive.chifact_start == 2.0

        assert "Starting chi factor is greater" in caplog.text
