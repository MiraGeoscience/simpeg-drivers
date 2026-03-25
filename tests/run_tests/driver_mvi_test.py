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

import contextlib
import logging
from pathlib import Path

import numpy as np
from dask.distributed import LocalCluster, performance_report
from geoh5py.groups import PropertyGroup
from geoh5py.groups.property_group import GroupTypeEnum
from geoh5py.objects import Curve
from geoh5py.workspace import Workspace
from simpeg.utils.mat_utils import cartesian2amplitude_dip_azimuth

from simpeg_drivers.components.factories import DirectivesFactory
from simpeg_drivers.potential_fields.magnetic_vector import (
    MagneticVectorForwardDriver,
    MagneticVectorForwardOptions,
    MagneticVectorInversionDriver,
    MagneticVectorInversionOptions,
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

target_mvi_run = {"data_norm": 149.1011743401604, "phi_d": 11.2, "phi_m": 0.0351}


def test_magnetic_vector_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="magnetic_vector",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        # Unitest dealing with Curve
        _ = Curve.create(
            geoh5, name=components.survey.name, vertices=components.survey.vertices
        )
        geoh5.remove_entity(components.survey)
        inducing_field = (50000.0, 90.0, 0.0)
        params = MagneticVectorForwardOptions.build(
            forward_only=True,
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            data_object=components.survey,
            starting_model=components.model,
            starting_inclination=45,
            starting_declination=270,
        )
    fwr_driver = MagneticVectorForwardDriver(params)
    fwr_driver.run()


def test_magnetic_vector_run(
    tmp_path: Path,
    caplog,
    max_iterations=3,
    upper_bound=2.5e-3,
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
        components = SyntheticsComponents(geoh5=geoh5)
        mesh = components.mesh
        topography = components.topography
        inducing_field = (50000.0, 90.0, 0.0)
        dip, direction = mesh.add_data(
            {
                "dip": {"values": np.ones(mesh.n_cells) * 45},
                "direction": {"values": np.ones(mesh.n_cells) * 90},
            }
        )
        gradient_rotation = PropertyGroup(
            name="gradient_rotations",
            property_group_type=GroupTypeEnum.DIPDIR,
            properties=[direction, dip],
            parent=mesh,
        )
        # Run the inverse
        with caplog.at_level(logging.WARNING) if caplog else contextlib.nullcontext():
            params = MagneticVectorInversionOptions.build(
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
                initial_beta_ratio=2e-2,
            )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        if caplog:
            assert "Deprecated field 'lower_bound' will be ignored." in caplog.text

    driver = MagneticVectorInversionDriver(params)
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
            assert np.isclose(driver.inversion.opt.upper[0], upper_bound)

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


def test_magnetic_vector_reference(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="magnetic_vector",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        tmi = components.survey.add_data(
            {"tmi": {"values": np.random.randn(components.survey.n_vertices)}}
        )
        inducing_field = (50000.0, 90.0, 0.0)
        params = MagneticVectorInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            tmi_channel=tmi,
            tmi_uncertainty=5.0,
            data_object=components.survey,
            starting_model=components.model,
            reference_model=0.0,
            reference_inclination=30,
            reference_declination=0,
        )
    driver = MagneticVectorInversionDriver(params)

    directives = DirectivesFactory(driver)
    assert np.all(directives.vector_inversion_directive.reference_angles)
    assert np.all(driver.models.reference_inclination == 30)
    assert np.all(driver.models.reference_declination == 0)

    ref_model = driver.models.reference_model
    ref_spherical = cartesian2amplitude_dip_azimuth(ref_model.reshape(-1, 3, order="F"))
    np.allclose(ref_spherical[0, 1], 30)
    np.allclose(ref_spherical[0, 2], 0)


if __name__ == "__main__":
    # Full run
    with LocalCluster(processes=True, n_workers=2, threads_per_worker=6) as cluster:
        with cluster.get_client():
            # Full run
            with performance_report(filename="diagnostics.html"):
                test_magnetic_vector_fwr_run(
                    Path("./"), n_grid_points=20, refinement=(4, 4)
                )
                test_magnetic_vector_run(
                    Path("./"), None, max_iterations=30, upper_bound=5e-3, pytest=False
                )
