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
from geoh5py.data import FloatData
from geoh5py.groups.property_group import GroupTypeEnum, PropertyGroup
from geoh5py.groups.simpeg import SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.joint.joint_petrophysics.driver import JointPetrophysicsDriver
from simpeg_drivers.joint.joint_petrophysics.options import JointPetrophysicsOptions
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
    MagneticInversionOptions,
    MVIForwardOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import (
    GravityForwardDriver,
    GravityInversionDriver,
)
from simpeg_drivers.potential_fields.magnetic_scalar.driver import (
    MagneticInversionDriver,
)
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MVIForwardDriver,
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
from tests.utils.targets import (
    check_target,
    get_inversion_output,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 390.70695894864303, "phi_d": 2020, "phi_m": 8.98}


def test_homogeneous_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
):
    # Create local problem A
    opts = SyntheticsComponentsOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=15.0
        ),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.75),
    )
    geoh5, mesh, model, survey, topography = SyntheticsComponents(
        tmp_path, method="gravity", options=opts
    )

    # Change half the model
    ind = mesh.centroids[:, 0] > 0
    model.values[ind] = 0.05

    params = GravityForwardOptions.build(
        geoh5=geoh5,
        mesh=mesh,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
    )
    fwr_driver_a = GravityForwardDriver(params)

    with geoh5.open():
        opts = SyntheticsComponentsOptions(
            survey=SurveyOptions(
                n_stations=n_grid_points, n_lines=n_grid_points, drape=15.0
            ),
            mesh=MeshOptions(refinement=refinement),
            model=ModelOptions(anomaly=0.05),
        )
        _, mesh, model, survey, _ = SyntheticsComponents(
            tmp_path, method="magnetic_vector", options=opts, geoh5=geoh5
        )
    inducing_field = (50000.0, 90.0, 0.0)
    # Change half the model
    ind = mesh.centroids[:, 0] > 0
    model.values[ind] = 0.01

    params = MVIForwardOptions.build(
        geoh5=geoh5,
        mesh=mesh,
        topography_object=topography,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        data_object=survey,
        starting_model=model,
    )
    fwr_driver_b = MVIForwardDriver(params)

    fwr_driver_a.run()
    fwr_driver_b.run()


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
        topography = geoh5.get_entity("topography")[0]
        drivers = []
        orig_data = []
        petrophysics = None
        gradient_rotation = None
        mesh = None
        for group_name in [
            "Gravity Forward",
            "Magnetic Vector Forward",
        ]:
            group = geoh5.get_entity(group_name)[0]

            if not isinstance(group, SimPEGGroup):
                continue

            mesh = group.get_entity("mesh")[0]
            survey = group.get_entity("survey")[0]

            if group_name == "Gravity Forward":
                global_mesh = mesh.copy(parent=geoh5)
                model = global_mesh.get_entity("starting_model")[0]

                mapping = {}
                vals = np.zeros_like(model.values, dtype=int)
                for ind, value in enumerate(np.unique(model.values)):
                    mapping[ind + 1] = f"Unit{ind}"
                    vals[model.values == value] = ind + 1

                topography = geoh5.get_entity("topography")[0]
                petrophysics = global_mesh.add_data(
                    {
                        "petrophysics": {
                            "values": vals,
                            "type": "REFERENCED",
                            "value_map": mapping,
                        }
                    }
                )
                dip, direction = global_mesh.add_data(
                    {
                        "dip": {"values": np.zeros(global_mesh.n_cells)},
                        "direction": {"values": np.zeros(global_mesh.n_cells)},
                    }
                )
                gradient_rotation = PropertyGroup(
                    name="gradient_rotations",
                    property_group_type=GroupTypeEnum.DIPDIR,
                    properties=[dip, direction],
                    parent=global_mesh,
                )

            data = None
            for child in survey.children:
                if isinstance(child, FloatData):
                    data = child

            if data is None:
                raise ValueError("No data found in survey")
            orig_data.append(data.values)

            ref_model = mesh.get_entity("starting_model")[0].copy(name="ref_model")
            ref_model.values = ref_model.values / 2.0

            if group.options["inversion_type"] == "gravity":
                params = GravityInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    topography_object=topography,
                    data_object=survey,
                    gz_channel=data,
                    gz_uncertainty=1e-2,
                    starting_model=ref_model,
                    reference_model=ref_model,
                )
                drivers.append(GravityInversionDriver(params))
            else:
                params = MagneticInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    topography_object=topography,
                    inducing_field_strength=group.options["inducing_field_strength"][
                        "value"
                    ],
                    inducing_field_inclination=group.options[
                        "inducing_field_inclination"
                    ]["value"],
                    inducing_field_declination=group.options[
                        "inducing_field_declination"
                    ]["value"],
                    data_object=survey,
                    starting_model=ref_model,
                    reference_model=ref_model,
                    tile_spatial=1,
                    tmi_channel=data,
                    tmi_uncertainty=5e0,
                )
                drivers.append(MagneticInversionDriver(params))

        params = JointPetrophysicsOptions.build(
            topography_object=topography,
            geoh5=geoh5,
            group_a=drivers[0].params.out_group,
            group_a_multiplier=1.0,
            group_b=drivers[1].params.out_group,
            group_b_multiplier=1.0,
            mesh=global_mesh,
            gradient_rotation=gradient_rotation,
            length_scale_x=1.0,
            length_scale_y=1.0,
            length_scale_z=1.0,
            petrophysical_model=petrophysics,
            initial_beta_ratio=1e2,
            max_global_iterations=max_iterations,
        )
        driver = JointPetrophysicsDriver(params)
        driver.run()

    if pytest:
        with Workspace(driver.params.geoh5.h5file) as run_ws:
            output = get_inversion_output(
                driver.params.geoh5.h5file, driver.params.out_group.uid
            )
            output["data"] = np.hstack(orig_data)
            check_target(output, target_run)

            out_group = run_ws.get_entity(driver.params.out_group.uid)[0]
            mesh = out_group.get_entity("mesh")[0]
            petro_model = mesh.get_entity("petrophysical_model")[0]
            assert len(np.unique(petro_model.values)) == 4


if __name__ == "__main__":
    # Full run
    test_homogeneous_fwr_run(
        Path("./"),
        n_grid_points=20,
        refinement=(4, 8),
    )

    test_homogeneous_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
