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
from dask.distributed import LocalCluster, performance_report
from geoh5py.workspace import Workspace

from simpeg_drivers.potential_fields import (
    MagneticForwardOptions,
    MagneticInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_scalar.driver import (
    MagneticForwardDriver,
    MagneticInversionDriver,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 8.71227951689941, "phi_d": 37.5, "phi_m": 5.72e-06}


def test_susceptibility_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="magnetic",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        inducing_field = (49999.8, 90.0, 0.0)

        params = MagneticForwardOptions.build(
            forward_only=True,
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            data_object=components.survey,
            starting_model=components.model,
        )
    # params.workpath = tmp_path
    fwr_driver = MagneticForwardDriver(params)
    fwr_driver.run()

    assert fwr_driver.inversion_data.survey.source_field.amplitude == inducing_field[0]

    assert params.out_group is not None
    assert params.out_group.options


def test_susceptibility_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_susceptibility_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        tmi = geoh5.get_entity("Iteration_0_tmi")[0]
        orig_tmi = tmi.values.copy()
        components = SyntheticsComponents(geoh5=geoh5)
        mesh = components.mesh
        active_cells = mesh.get_entity("active_cells")[0]
        inducing_field = (50000.0, 90.0, 0.0)

        # Run the inverse
        params = MagneticInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            active_model=active_cells,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            data_object=tmi.parent,
            starting_model=1e-4,
            reference_model=0.0,
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            initial_beta_ratio=1e1,
            tmi_channel=tmi,
            tmi_uncertainty=1.0,
            max_global_iterations=max_iterations,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    assert params.models.lower_bound == 0.0
    driver = MagneticInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with Workspace(driver.params.geoh5.h5file) as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_tmi
        assert (
            run_ws.get_entity("Iteration_1_tmi")[0].entity_type.uid
            == run_ws.get_entity("Observed_tmi")[0].entity_type.uid
        )

        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    with LocalCluster(processes=True, n_workers=2, threads_per_worker=6) as cluster:
        with cluster.get_client():
            # Full run
            with performance_report(filename="diagnostics.html"):
                test_susceptibility_fwr_run(
                    Path("./"), n_grid_points=20, refinement=(4, 8)
                )
                test_susceptibility_run(Path("./"), max_iterations=30, pytest=False)
