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

from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.locations import gaussian
from geoh5py.groups.property_group import PropertyGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.potential_fields.gravity import (
    GravityForwardDriver,
    GravityForwardOptions,
    GravityInversionDriver,
    GravityInversionOptions,
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
# pylint: disable=no-member

target_run = {"data_norm": 0.3337151941623077, "phi_d": 23600, "phi_m": 7.54}


def test_gravity_rotated_grad_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    cell_size=(20.0, 20.0, 20.0),
    refinement=(2,),
):
    # Run the forward

    opts = SyntheticsComponentsOptions(
        method="gravity",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points,
            n_lines=n_grid_points,
            center=(0.0, 0.0),
            drape=5.0,
            topography=lambda x, y: gaussian(x, y, amplitude=50.0, width=100.0) + 15,
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
        ),
        model=ModelOptions(
            anomaly=0.75,
            plate=PlateModel(
                strike_length=500.0,
                dip_length=150.0,
                width=20.0,
                easting=0.0,
                northing=0.0,
                elevation=-10.0,
                direction=60.0,
                dip=70.0,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        params = GravityForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            gz_channel_bool=True,
        )
    fwr_driver = GravityForwardDriver(params)
    fwr_driver.run()


def test_rotated_grad_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_gravity_rotated_grad_fwr_0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        gz = geoh5.get_entity("Iteration_0_gz")[0]
        orig_gz = gz.values.copy()
        components = SyntheticsComponents(geoh5=geoh5)
        mesh = components.mesh
        topography = components.topography

        # Create property group with orientation
        dip = np.ones(mesh.n_cells) * 70
        azimuth = np.ones(mesh.n_cells) * 60

        data_list = mesh.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            mesh, properties=data_list, property_group_type="Dip direction & dip"
        )

        # Run the inverse
        params = GravityInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=topography,
            data_object=gz.parent,
            gradient_rotation=pg,
            starting_model=1e-4,
            reference_model=0.0,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            gz_channel=gz,
            gz_uncertainty=2e-3,
            lower_bound=0.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-1,
            percentile=95,
            save_sensitivities=True,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = GravityInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with Workspace(driver.params.geoh5.h5file) as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_gz

        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)

    # Smooth functions should be zero for uniform model
    for obj in driver.regularization.objfcts:
        for smooth in obj.objfcts[1:]:
            np.testing.assert_allclose(
                smooth(np.ones(driver.models.n_active)), 0, atol=1e-6
            )


if __name__ == "__main__":
    # Full run
    test_gravity_rotated_grad_fwr_run(
        Path("./"),
        n_grid_points=10,
        cell_size=(20.0, 20.0, 20.0),
        refinement=(6, 8),
    )

    test_rotated_grad_run(
        Path("./"),
        max_iterations=40,
        pytest=False,
    )
