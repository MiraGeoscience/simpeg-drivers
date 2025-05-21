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
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.workspace import Workspace
from pytest import raises

from simpeg_drivers.joint.joint_petrophysics.driver import JointPetrophysicsDriver
from simpeg_drivers.joint.joint_petrophysics.options import JointPetrophysicsOptions
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import GravityForwardDriver
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.0028055269276044915, "phi_d": 8.32e-05, "phi_m": 0.0038}


def test_homogeneous_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.75,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        flatten=False,
    )
    # with geoh5.open():
    #     model.values[(mesh.centroids[:, 0] > 0) & (model.values == 0)] = -0.1
    #     geoh5.update_attribute(model, "values")

    active_cells = ActiveCellsOptions(topography_object=topography)
    params = GravityForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=active_cells,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
        gz_channel_bool=True,
    )
    fwr_driver = GravityForwardDriver(params)
    fwr_driver.run()


def test_homogeneous_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_homogeneous_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath, mode="r+") as geoh5:
        gz = geoh5.get_entity("Iteration_0_gz")[0]

        mesh = geoh5.get_entity("mesh")[0]
        model = mesh.get_entity("starting_model")[0]

        mapping = {}
        vals = np.zeros_like(model.values, dtype=int)
        for ind, value in enumerate(np.unique(model.values)):
            mapping[ind + 1] = f"Unit{ind}"
            vals[model.values == value] = ind + 1

        topography = geoh5.get_entity("topography")[0]
        petrophysics = mesh.add_data(
            {
                "petrophysics": {
                    "values": vals,
                    "type": "REFERENCED",
                    "value_map": mapping,
                }
            }
        )

        # Run the inverse
        active_cells = ActiveCellsOptions(topography_object=topography)
        GravityInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=active_cells,
            data_object=gz.parent,
            starting_model=1e-4,
            reference_model=model,
            gz_channel=gz,
            gz_uncertainty=2e-3,
            lower_bound=0.0,
            store_sensitivities="ram",
            save_sensitivities=True,
        )

        grav_group = geoh5.get_entity("Gravity Inversion")[0]

        params = JointPetrophysicsOptions(
            active_cells=active_cells,
            geoh5=geoh5,
            group_a=grav_group,
            mesh=mesh,
            petrophysics_model=petrophysics,
            initial_beta_ratio=1e2,
            length_scale_x=0.0,
            length_scale_y=0.0,
            length_scale_z=0.0,
            max_global_iterations=max_iterations,
        )
        driver = JointPetrophysicsDriver(params)
        driver.run()

    # with Workspace(driver.params.geoh5.h5file) as run_ws:
    #     output = get_inversion_output(
    #         driver.params.geoh5.h5file, driver.params.out_group.uid
    #     )
    #
    #     if pytest:
    #         check_target(output, target_run)
    #         nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
    #         inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
    #         assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_homogeneous_fwr_run(
        Path("./"),
        n_grid_points=20,
        refinement=(4, 8),
    )

    test_homogeneous_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
