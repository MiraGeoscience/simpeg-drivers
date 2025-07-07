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
from unittest.mock import patch

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.groups.property_group import PropertyGroup
from geoh5py.workspace import Workspace
from pytest import raises

from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import (
    GravityForwardDriver,
    GravityInversionDriver,
)
from simpeg_drivers.utils.utils import get_inversion_output
from tests.testing_utils import check_target, setup_inversion_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.40763989924638555, "phi_d": 1040, "phi_m": 104}


def test_gravity_rotated_grad_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    plate_model = PlateModel(
        strike_length=500.0,
        dip_length=150.0,
        width=20.0,
        origin=(0.0, 0.0, -10.0),
        direction=60.0,
        dip=70.0,
    )
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        plate_model=plate_model,
        background=0.0,
        anomaly=0.75,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        center=(0.0, 0.0, 15.0),
        flatten=False,
    )

    params = GravityForwardOptions.build(
        geoh5=geoh5,
        mesh=model.parent,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
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
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

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
        refinement=(6, 8),
    )

    test_rotated_grad_run(
        Path("./"),
        max_iterations=40,
        pytest=False,
    )
