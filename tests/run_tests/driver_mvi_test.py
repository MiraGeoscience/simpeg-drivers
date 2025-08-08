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

import contextlib
import logging
from pathlib import Path

import numpy as np
from geoh5py.groups import PropertyGroup
from geoh5py.groups.property_group import GroupTypeEnum
from geoh5py.objects import Curve
from geoh5py.workspace import Workspace

from simpeg_drivers.potential_fields import (
    MVIForwardOptions,
    MVIInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MVIForwardDriver,
    MVIInversionDriver,
)
from simpeg_drivers.utils.testing_utils.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticDataInversionOptions,
)
from simpeg_drivers.utils.testing_utils.runtests import (
    setup_inversion_workspace,
)
from simpeg_drivers.utils.testing_utils.targets import (
    check_target,
    get_inversion_output,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_mvi_run = {"data_norm": 149.10117594929326, "phi_d": 58.6, "phi_m": 0.0079}


def test_magnetic_vector_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
):
    # Run the forward
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    geoh5, _, model, points, topography = setup_inversion_workspace(
        tmp_path, method="magnetic_vector", options=opts
    )

    # Unitest dealing with Curve
    with geoh5.open():
        survey = Curve.create(geoh5, name=points.name, vertices=points.vertices)
        geoh5.remove_entity(points)
    inducing_field = (50000.0, 90.0, 0.0)
    params = MVIForwardOptions.build(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent,
        topography_object=topography,
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
    caplog,
    max_iterations=3,
    upper_bound=2e-3,
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
        dip, direction = mesh.add_data(
            {
                "dip": {"values": np.zeros(mesh.n_cells)},
                "direction": {"values": np.zeros(mesh.n_cells)},
            }
        )
        gradient_rotation = PropertyGroup(
            name="gradient_rotations",
            property_group_type=GroupTypeEnum.DIPDIR,
            properties=[dip, direction],
            parent=mesh,
        )
        # Run the inverse
        with caplog.at_level(logging.WARNING) if caplog else contextlib.nullcontext():
            params = MVIInversionOptions.build(
                geoh5=geoh5,
                mesh=mesh,
                topography_object=topography,
                inducing_field_strength=inducing_field[0],
                inducing_field_inclination=inducing_field[1],
                inducing_field_declination=inducing_field[2],
                data_object=tmi.parent,
                starting_model=1e-4,
                reference_model=0.0,
                gradient_rotation=gradient_rotation,
                s_norm=0.0,
                x_norm=1.0,
                y_norm=1.0,
                z_norm=1.0,
                tmi_channel=tmi,
                tmi_uncertainty=5.0,
                lower_bound=1e-6,
                upper_bound=upper_bound,
                max_global_iterations=max_iterations,
                initial_beta_ratio=1e1,
            )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        if caplog:
            assert "Skipping deprecated field: lower_bound" in caplog.text

    driver = MVIInversionDriver(params)
    assert np.all(driver.models.lower_bound == -upper_bound)
    driver.run()

    if pytest:
        with Workspace(driver.params.geoh5.h5file) as run_ws:
            # Re-open the workspace and get iterations
            output = get_inversion_output(
                driver.params.geoh5.h5file, driver.params.out_group.uid
            )
            output["data"] = orig_tmi
            model = run_ws.get_entity("Iteration_3_amplitude_model")[0]
            nan_ind = np.isnan(model.values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)

            assert np.nanmin(model.values) <= 1e-5
            assert np.isclose(np.nanmax(model.values), upper_bound)

            out_group = run_ws.get_entity("Magnetic Vector Inversion")[0]
            mesh = out_group.get_entity("mesh")[0]
            assert len(mesh.property_groups) == 6
            assert len(mesh.fetch_property_group("Iteration_0").properties) == 2
            assert len(mesh.fetch_property_group("LP models").properties) == 6
            assert (
                mesh.fetch_property_group("Iteration_1").property_group_type
                == GroupTypeEnum.DIPDIR
            )
            check_target(output, target_mvi_run)


if __name__ == "__main__":
    # Full run
    test_magnetic_vector_fwr_run(Path("./"), n_grid_points=20, refinement=(4, 8))
    test_magnetic_vector_run(
        Path("./"), None, max_iterations=30, upper_bound=1e-1, pytest=False
    )
