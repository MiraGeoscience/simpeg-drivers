# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoh5py.workspace import Workspace

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver import (
    SensitivityCutoffDriver,
)
from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.params import (
    SensitivityCutoffParams,
)
from simpeg_drivers.potential_fields import GravityParams
from simpeg_drivers.potential_fields.gravity.driver import GravityDriver
from simpeg_drivers.utils.testing import setup_inversion_workspace


def test_gravity_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.75,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        flatten=False,
    )
    params = GravityParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
    )
    fwr_driver = GravityDriver(params)
    fwr_driver.run()


def test_gravity_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_gravity_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        gz = geoh5.get_entity("Iteration_0_gz")[0]
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = GravityParams(
            geoh5=geoh5,
            mesh=mesh.uid,
            topography_object=topography.uid,
            data_object=gz.parent.uid,
            starting_model=1e-4,
            reference_model=0.0,
            s_norm=0.0,
            gradient_type="components",
            gz_channel_bool=True,
            z_from_topo=False,
            gz_channel=gz.uid,
            gz_uncertainty=2e-3,
            lower_bound=0.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-2,
            prctile=100,
            store_sensitivities="ram",
            save_sensitivities=True,
        )
        params.write_input_file(path=tmp_path, name="Inv_run")

    GravityDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with Workspace(workpath) as geoh5:
        sensitivity = geoh5.get_entity("Iteration_1_sensitivities")[0]
        mesh = sensitivity.parent

        params = SensitivityCutoffParams(
            geoh5=geoh5,
            mesh=mesh,
            sensitivity_model=sensitivity,
            sensitivity_cutoff=1,
            cutoff_method="percent",
            mask_name="5 percent cutoff",
        )
        params.write_ui_json(path=tmp_path / "sensitivity_cutoff_percent")

    SensitivityCutoffDriver.start(str(tmp_path / "sensitivity_cutoff_percent.ui.json"))

    with Workspace(workpath) as geoh5:
        # mask = geoh5.get_entity("5 percent cutoff")[0]
        # assert mask.values.sum() == 1355

        params = SensitivityCutoffParams(
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

    with Workspace(workpath) as geoh5:
        mask = geoh5.get_entity("5 percentile cutoff")[0]
        assert mask.values.sum() == 22861

        params = SensitivityCutoffParams(
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

    with Workspace(workpath) as geoh5:
        mask = geoh5.get_entity("5 percent log cutoff")[0]
        assert mask.values.sum() == 23144
