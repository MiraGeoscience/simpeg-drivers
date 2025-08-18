# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import numpy as np
from geoh5py.data import FloatData
from geoh5py.groups import SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DC3DForwardOptions,
    DC3DInversionOptions,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.driver import (
    DC3DForwardDriver,
    DC3DInversionDriver,
)
from simpeg_drivers.joint.joint_cross_gradient import JointCrossGradientOptions
from simpeg_drivers.joint.joint_cross_gradient.driver import JointCrossGradientDriver
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
    MVIForwardOptions,
    MVIInversionOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import (
    GravityForwardDriver,
    GravityInversionDriver,
)
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MVIForwardDriver,
    MVIInversionDriver,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    ActiveCellsOptions as SyntheticsActiveCellsOptions,
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

target_run = {"data_norm": 53.29585552088844, "phi_d": 7970, "phi_m": 26.7}
INDUCING_FIELD = (50000.0, 90.0, 0.0)


def test_joint_cross_gradient_fwr_run(
    tmp_path,
    n_grid_points=4,
    n_lines=3,
    refinement=(2,),
):
    # Create local problem A
    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=15.0, name="survey A"
        ),
        mesh=MeshOptions(refinement=refinement, name="mesh A"),
        model=ModelOptions(anomaly=0.75, name="model A"),
        active=SyntheticsActiveCellsOptions(name="active A"),
    )
    with Workspace.create(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = GravityForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver_a = GravityForwardDriver(params)

    with geoh5.open():
        opts = SyntheticsComponentsOptions(
            method="magnetic_vector",
            survey=SurveyOptions(
                n_stations=n_grid_points,
                n_lines=n_grid_points,
                drape=15.0,
                name="survey B",
            ),
            mesh=MeshOptions(refinement=refinement, name="mesh B"),
            model=ModelOptions(anomaly=0.05, name="model B"),
            active=SyntheticsActiveCellsOptions(name="active B"),
        )
        components = SyntheticsComponents(geoh5, options=opts)
        params = MVIForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=INDUCING_FIELD[0],
            inducing_field_inclination=INDUCING_FIELD[1],
            inducing_field_declination=INDUCING_FIELD[2],
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver_b = MVIForwardDriver(params)

    with geoh5.open():
        opts = SyntheticsComponentsOptions(
            method="direct current 3d",
            survey=SurveyOptions(
                n_stations=n_grid_points, n_lines=n_lines, name="survey C"
            ),
            mesh=MeshOptions(refinement=refinement, name="mesh C"),
            model=ModelOptions(background=0.01, anomaly=10, name="model C"),
            active=SyntheticsActiveCellsOptions(name="active C"),
        )
        components = SyntheticsComponents(geoh5, options=opts)

        params = DC3DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver_c = DC3DForwardDriver(params)

    with geoh5.open():
        fwr_driver_c.inversion_data.entity.name = "survey C"

        # Force co-location of meshes
        for driver in [fwr_driver_b, fwr_driver_c]:
            driver.inversion_mesh.entity.origin = (
                fwr_driver_a.inversion_mesh.entity.origin
            )
            driver.workspace.update_attribute(
                driver.inversion_mesh.entity, "attributes"
            )
            driver.inversion_mesh._mesh = None  # pylint: disable=protected-access

    fwr_driver_a.run()
    fwr_driver_b.run()
    fwr_driver_c.run()


def test_joint_cross_gradient_inv_run(
    tmp_path,
    max_iterations=1,
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

        for suffix in "ABC":
            components = SyntheticsComponents(
                geoh5=geoh5,
                options=SyntheticsComponentsOptions(
                    method="joint",
                    survey=SurveyOptions(name=f"survey {suffix}"),
                    mesh=MeshOptions(name=f"mesh {suffix}"),
                    model=ModelOptions(name=f"model {suffix}"),
                    active=SyntheticsActiveCellsOptions(name=f"active {suffix}"),
                ),
            )

            mesh = components.mesh
            survey = components.survey
            data = next([k for k in survey.children if "Iteration_0" in k.name])
            orig_data.append(data.values)

            if suffix == "A":
                params = GravityInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    data_object=survey,
                    gz_channel=data,
                    gz_uncertainty=1e-2,
                    starting_model=0.0,
                    reference_model=0.0,
                )
                drivers.append(GravityInversionDriver(params))
            elif suffix == "C":
                params = DC3DInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    data_object=survey,
                    potential_channel=data,
                    model_type="Resistivity (Ohm-m)",
                    potential_uncertainty=5e-4,
                    tile_spatial=1,
                    starting_model=100.0,
                    reference_model=100.0,
                    save_sensitivities=True,
                    solver_type="Mumps",
                )
                drivers.append(DC3DInversionDriver(params))
            else:
                params = MVIInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    inducing_field_strength=INDUCING_FIELD[0],
                    inducing_field_inclination=INDUCING_FIELD[1],
                    inducing_field_declination=INDUCING_FIELD[2],
                    data_object=survey,
                    starting_model=1e-4,
                    reference_model=0.0,
                    tile_spatial=1,
                    tmi_channel=data,
                    tmi_uncertainty=1e1,
                )
                drivers.append(MVIInversionDriver(params))

        # Run the inverse
        joint_params = JointCrossGradientOptions.build(
            geoh5=geoh5,
            topography_object=topography,
            group_a=drivers[0].params.out_group,
            group_a_multiplier=1.0,
            group_b=drivers[1].params.out_group,
            group_b_multiplier=1.0,
            group_c=drivers[2].params.out_group,
            group_c_multiplier=1.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            cross_gradient_weight_a_b=1e0,
            cross_gradient_weight_c_a=1e0,
            cross_gradient_weight_c_b=1e0,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            percentile=100,
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
        pytest=False,
    )
