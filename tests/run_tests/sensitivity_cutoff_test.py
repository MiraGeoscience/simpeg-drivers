# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2025 Mira Geoscience Ltd.                                     '
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
from geoh5py.workspace import Workspace

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver import (
    SensitivityCutoffDriver,
)
from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.options import (
    SensitivityCutoffOptions,
)
from simpeg_drivers.potential_fields import GravityInversionOptions
from simpeg_drivers.potential_fields.gravity.driver import GravityInversionDriver
from simpeg_drivers.utils.synthetics.driver import setup_inversion_workspace
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)


def setup_inversion_results(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    opts = SyntheticsComponentsOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.75),
    )
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="gravity", options=opts
    )

    # Run the inverse with save_sensitivities=True
    with geoh5.open():
        gz = survey.add_data({"gz": {"values": np.random.randn(len(survey.vertices))}})

    params = GravityInversionOptions.build(
        geoh5=geoh5,
        mesh=mesh,
        topography_object=topography,
        data_object=gz.parent,
        starting_model=1e-4,
        reference_model=0.0,
        s_norm=0.0,
        gz_channel=gz,
        gz_uncertainty=2e-3,
        lower_bound=0.0,
        max_global_iterations=1,
        initial_beta_ratio=1e-2,
        percentile=100,
        save_sensitivities=True,
    )
    params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
    GravityInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))


def test_sensitivity_percent_cutoff_run(tmp_path):
    setup_inversion_results(
        tmp_path,
        n_grid_points=2,
        refinement=(2,),
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = sensitivity.parent
        params = SensitivityCutoffOptions(
            geoh5=geoh5,
            mesh=mesh,
            sensitivity_model=sensitivity,
            sensitivity_cutoff=1,
            cutoff_method="percent",
            mask_name="5 percent cutoff",
        )
        params.write_ui_json(path=tmp_path / "sensitivity_cutoff_percent")

    SensitivityCutoffDriver.start(str(tmp_path / "sensitivity_cutoff_percent.ui.json"))
    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        mask = geoh5.get_entity("5 percent cutoff")[0]
        assert mask.values.sum() == 1355


def test_sensitivity_cutoff_percentile_run(tmp_path):
    setup_inversion_results(
        tmp_path,
        n_grid_points=2,
        refinement=(2,),
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = sensitivity.parent
        params = SensitivityCutoffOptions(
            geoh5=geoh5,
            mesh=mesh,
            sensitivity_model=sensitivity,
            sensitivity_cutoff=1,
            cutoff_method="percentile",
            mask_name="5 percentile cutoff",
        )
        params.write_ui_json(path=tmp_path / "sensitivity_cutoff_percentile")

    SensitivityCutoffDriver.start(
        str(tmp_path / "sensitivity_cutoff_percentile.ui.json")
    )
    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        mask = geoh5.get_entity("5 percentile cutoff")[0]
        assert mask.values.sum() == 22861


def test_sensitivity_cutoff_log_percent_run(tmp_path):
    setup_inversion_results(
        tmp_path,
        n_grid_points=2,
        refinement=(2,),
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = sensitivity.parent
        params = SensitivityCutoffOptions(
            geoh5=geoh5,
            mesh=mesh,
            sensitivity_model=sensitivity,
            sensitivity_cutoff=1,
            cutoff_method="log_percent",
            mask_name="5 percent log cutoff",
        )
        params.write_ui_json(path=tmp_path / "sensitivity_cutoff_log_percent")

    SensitivityCutoffDriver.start(
        str(tmp_path / "sensitivity_cutoff_log_percent.ui.json")
    )
    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        mask = geoh5.get_entity("5 percent log cutoff")[0]
        assert mask.values.sum() == 23144
