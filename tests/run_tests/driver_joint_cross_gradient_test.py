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

from pathlib import Path

import numpy as np
from geoh5py.data import FloatData
from geoh5py.groups import SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DirectCurrent3DParams,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.driver import (
    DirectCurrent3DDriver,
)
from simpeg_drivers.joint.joint_cross_gradient import JointCrossGradientParams
from simpeg_drivers.joint.joint_cross_gradient.driver import JointCrossGradientDriver
from simpeg_drivers.potential_fields import GravityParams, MagneticVectorParams
from simpeg_drivers.potential_fields.gravity.driver import GravityDriver
from simpeg_drivers.potential_fields.magnetic_vector.driver import MagneticVectorDriver
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output

# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 53.29600188902931, "phi_d": 500, "phi_m": 0.1585}


def test_joint_cross_gradient_fwr_run(
    tmp_path,
    n_grid_points=4,
    n_lines=3,
    refinement=(2,),
):
    # Create local problem A
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.75,
        drape_height=15.0,
        refinement=refinement,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
    )
    params = GravityParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        resolution=0.0,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
    )
    fwr_driver_a = GravityDriver(params)

    _, _, model, survey, _ = setup_inversion_workspace(
        tmp_path,
        geoh5=geoh5,
        background=0.0,
        anomaly=0.05,
        drape_height=15.0,
        refinement=refinement,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        flatten=False,
    )
    inducing_field = (50000.0, 90.0, 0.0)
    params = MagneticVectorParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        resolution=0.0,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
    )
    params.workpath = tmp_path
    fwr_driver_b = MagneticVectorDriver(params)

    _, _, model, survey, _ = setup_inversion_workspace(
        tmp_path,
        geoh5=geoh5,
        background=0.01,
        anomaly=10,
        n_electrodes=n_grid_points,
        n_lines=n_lines,
        refinement=refinement,
        drape_height=0.0,
        inversion_type="dcip",
        flatten=False,
    )
    params = DirectCurrent3DParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        data_object=survey.uid,
        starting_model=model.uid,
    )
    fwr_driver_c = DirectCurrent3DDriver(params)
    fwr_driver_c.inversion_data.entity.name = "survey"

    # Force co-location of meshes
    for driver in [fwr_driver_b, fwr_driver_c]:
        driver.inversion_mesh.entity.origin = fwr_driver_a.inversion_mesh.entity.origin
        driver.workspace.update_attribute(driver.inversion_mesh.entity, "attributes")
        driver.inversion_mesh._mesh = None  # pylint: disable=protected-access

    fwr_driver_a.run()
    fwr_driver_b.run()
    fwr_driver_c.run()


def test_joint_cross_gradient_inv_run(
    tmp_path,
    max_iterations=1,
    n_lines=3,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_joint_cross_gradient_fwr_0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        topography = geoh5.get_entity("topography")[0]
        drivers = []
        orig_data = []

        for group_name in [
            "Gravity Forward",
            "Magnetic vector Forward",
            "Direct current 3d Forward",
        ]:
            group = geoh5.get_entity(group_name)[0]

            if not isinstance(group, SimPEGGroup):
                continue

            mesh = group.get_entity("mesh")[0]
            survey = group.get_entity("survey")[0]

            data = None
            for child in survey.children:
                if isinstance(child, FloatData):
                    data = child

            assert data is not None, "Could not find data object."

            orig_data.append(data.values)

            if group.options["inversion_type"] == "gravity":
                params = GravityParams(
                    geoh5=geoh5,
                    mesh=mesh.uid,
                    alpha_s=0.0,
                    topography_object=topography.uid,
                    data_object=survey.uid,
                    gz_channel=data.uid,
                    gz_uncertainty=1e-3,
                    starting_model=0.0,
                )
                drivers.append(GravityDriver(params))
            elif group.options["inversion_type"] == "direct current 3d":
                params = DirectCurrent3DParams(
                    geoh5=geoh5,
                    mesh=mesh.uid,
                    alpha_s=0.0,
                    topography_object=topography.uid,
                    data_object=survey.uid,
                    potential_channel=data.uid,
                    potential_uncertainty=1e-3,
                    tile_spatial=n_lines,
                    starting_model=1e-2,
                    reference_model=1e-2,
                )
                drivers.append(DirectCurrent3DDriver(params))
            else:
                params = MagneticVectorParams(
                    geoh5=geoh5,
                    mesh=mesh.uid,
                    alpha_s=0.0,
                    topography_object=topography.uid,
                    inducing_field_strength=group.options["inducing_field_strength"][
                        "value"
                    ],
                    inducing_field_inclination=group.options[
                        "inducing_field_inclination"
                    ]["value"],
                    inducing_field_declination=group.options[
                        "inducing_field_declination"
                    ]["value"],
                    data_object=survey.uid,
                    starting_model=1e-4,
                    reference_model=0.0,
                    tile_spatial=1,
                    tmi_channel=data.uid,
                    tmi_uncertainty=1e0,
                )
                drivers.append(MagneticVectorDriver(params))

        # Run the inverse
        joint_params = JointCrossGradientParams(
            geoh5=geoh5,
            topography_object=topography.uid,
            group_a=drivers[0].params.out_group,
            group_a_multiplier=1e-2,
            group_b=drivers[1].params.out_group,
            group_b_multiplier=1e-2,
            group_c=drivers[2].params.out_group,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e2,
            cross_gradient_weight_a_b=5e0,
            cross_gradient_weight_c_a=5e0,
            cross_gradient_weight_c_b=5e0,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            gradient_type="components",
            prctile=100,
            store_sensitivities="ram",
        )

    driver = JointCrossGradientDriver(joint_params)
    driver.run()

    with Workspace(driver.params.geoh5.h5file):
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )

        output["data"] = np.hstack(orig_data)
        if pytest:
            check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_joint_cross_gradient_fwr_run(
        Path("./"),
        n_grid_points=16,
        n_lines=5,
        refinement=(4, 8),
    )
    test_joint_cross_gradient_inv_run(
        Path("./"),
        max_iterations=20,
        n_lines=5,
        pytest=False,
    )
