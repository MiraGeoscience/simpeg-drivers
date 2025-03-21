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
from geoh5py.groups.property_group import GroupTypeEnum
from geoh5py.objects import Curve
from geoh5py.workspace import Workspace

from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.potential_fields import (
    MVIForwardOptions,
    MVIInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MVIForwardDriver,
    MVIInversionDriver,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_mvi_run = {"data_norm": 6.3559205278626525, "phi_d": 0.0143, "phi_m": 0.0009}


def test_magnetic_vector_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    geoh5, _, model, points, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=refinement,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
    )

    # Unitest dealing with Curve
    with geoh5.open():
        survey = Curve.create(geoh5, name=points.name, vertices=points.vertices)
        geoh5.remove_entity(points)
    inducing_field = (50000.0, 90.0, 0.0)
    active_cells = ActiveCellsOptions(topography_object=topography)
    params = MVIForwardOptions(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=active_cells,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        data_object=survey,
        starting_model=model,
        starting_inclination=45,
        starting_declination=270,
    )
    fwr_driver = MVIForwardDriver(params)
    fwr_driver.run()


def test_magnetic_vector_run(
    tmp_path: Path,
    max_iterations=2,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_magnetic_vector_fwr_run0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        tmi = geoh5.get_entity("Iteration_0_tmi")[0]
        orig_tmi = tmi.values.copy()
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]
        inducing_field = (50000.0, 90.0, 0.0)

        # Run the inverse
        active_cells = ActiveCellsOptions(topography_object=topography)
        params = MVIInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=active_cells,
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
            gradient_type="components",
            tmi_channel=tmi,
            tmi_uncertainty=4.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            store_sensitivities="ram",
            save_sensitivities=True,
            percentile=100,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = MVIInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with Workspace(driver.params.geoh5.h5file) as run_ws:
        # Re-open the workspace and get iterations
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_tmi
        if pytest:
            check_target(output, target_mvi_run)
            nan_ind = np.isnan(
                run_ws.get_entity("Iteration_0_amplitude_model")[0].values
            )
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)

        out_group = run_ws.get_entity("Magnetic Vector Inversion")[0]
        mesh = out_group.get_entity("mesh")[0]
        assert len(mesh.property_groups) == 3
        assert len(mesh.property_groups[0].properties) == 2
        assert mesh.property_groups[1].property_group_type == GroupTypeEnum.DIPDIR


if __name__ == "__main__":
    # Full run
    test_magnetic_vector_fwr_run(Path("./"), n_grid_points=20, refinement=(4, 8))
    test_magnetic_vector_run(Path("./"), max_iterations=30, pytest=False)
