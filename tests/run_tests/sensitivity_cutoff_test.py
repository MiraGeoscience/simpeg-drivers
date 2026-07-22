# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from geoh5py.workspace import Workspace

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver import (
    SensitivityCutoffDriver,
)
from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.options import (
    SensitivityCutoffOptions,
)
from simpeg_drivers.potential_fields.gravity.inversion import (
    GravityInversionDriver,
    GravityInversionOptions,
)
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import get_workspace


def setup_inversion_results(
    tmp_path: Path,
    n_grid_points=2,
    cell_size=(20.0, 20.0, 20.0),
    refinement=(2,),
):
    opts = SyntheticsComponentsOptions(
        method="gravity",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
        ),
        model=ModelOptions(anomaly=0.75),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        # Run the inverse with save_sensitivities=True
        gz = components.survey.add_data(
            {"gz": {"values": np.random.randn(len(components.survey.vertices))}}
        )

        # Shift some vertices to avoid 0 sensititives
        verts = components.survey.vertices
        verts[:, 2] += np.arange(len(verts))

        components.survey.vertices = verts

        params = GravityInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
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


def test_setup_inversion_results(tmp_path: Path):
    setup_inversion_results(
        tmp_path,
        n_grid_points=2,
        refinement=(2,),
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        assert sensitivity is not None


def test_sensitivity_percent_cutoff_run(tmp_path):
    shutil.copy(
        tmp_path / "../test_setup_inversion_results0/inversion_test.ui.geoh5",
        tmp_path / "inversion_test.ui.geoh5",
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5)
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = components.mesh
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
        assert mask.values.sum() == 525


def test_sensitivity_cutoff_percentile_run(tmp_path):
    shutil.copy(
        tmp_path / "../test_setup_inversion_results0/inversion_test.ui.geoh5",
        tmp_path / "inversion_test.ui.geoh5",
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5)
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = components.mesh
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
        assert mask.values.sum() == 792


def test_sensitivity_cutoff_log_percent_run(tmp_path):
    shutil.copy(
        tmp_path / "../test_setup_inversion_results0/inversion_test.ui.geoh5",
        tmp_path / "inversion_test.ui.geoh5",
    )

    with Workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5)
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = components.mesh
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
        assert mask.values.sum() == 798
