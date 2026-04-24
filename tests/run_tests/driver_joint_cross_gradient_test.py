# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import logging
from pathlib import Path

import numpy as np
from geoh5py.groups import GroupTypeEnum, PropertyGroup
from geoh5py.objects import CurrentElectrode, Octree, Points
from geoh5py.workspace import Workspace
from simpeg.directives import UpdateIRLS

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DC3DForwardDriver,
    DC3DForwardOptions,
    DC3DInversionDriver,
    DC3DInversionOptions,
)
from simpeg_drivers.joint.joint_cross_gradient.driver import JointCrossGradientDriver
from simpeg_drivers.joint.joint_cross_gradient.options import JointCrossGradientOptions
from simpeg_drivers.potential_fields.gravity import (
    GravityForwardDriver,
    GravityForwardOptions,
    GravityInversionDriver,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_vector import (
    MagneticVectorForwardDriver,
    MagneticVectorForwardOptions,
    MagneticVectorInversionDriver,
    MagneticVectorInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_vector_pde import (
    MagneticVectorPDEInversionDriver,
    MagneticVectorPDEInversionOptions,
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
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 53.31483800448377, "phi_d": 558, "phi_m": 0.0574}
INDUCING_FIELD = (50000.0, 90.0, 0.0)


def test_joint_cross_gradient_fwr_run(
    tmp_path,
    n_grid_points=4,
    n_lines=3,
    cell_size=(20.0, 20.0, 20.0),
    refinement=(2,),
):
    # Create local problem A
    opts = SyntheticsComponentsOptions(
        method="gravity",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=15.0, name="survey A"
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
            name="mesh A",
        ),
        model=ModelOptions(anomaly=0.75, name="model A"),
        active=SyntheticsActiveCellsOptions(name="active A"),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
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
            refine_plate=True,
            survey=SurveyOptions(
                n_stations=n_grid_points,
                n_lines=n_grid_points,
                drape=15.0,
                name="survey B",
            ),
            mesh=MeshOptions(
                u_cell_size=cell_size[0],
                v_cell_size=cell_size[1],
                w_cell_size=cell_size[2],
                survey_refinement=list(refinement),
                topography_refinement=[0, 0, 1],
                plate_refinement=[1],
                name="mesh B",
            ),
            model=ModelOptions(anomaly=0.05, name="model B"),
            active=SyntheticsActiveCellsOptions(name="active B"),
        )
        components = SyntheticsComponents(geoh5, options=opts)
        params = MagneticVectorForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=INDUCING_FIELD[0],
            inducing_field_inclination=INDUCING_FIELD[1],
            inducing_field_declination=INDUCING_FIELD[2],
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver_b = MagneticVectorForwardDriver(params)

    with geoh5.open():
        opts = SyntheticsComponentsOptions(
            method="direct current 3d",
            refine_plate=True,
            survey=SurveyOptions(
                n_stations=n_grid_points, n_lines=n_lines, name="survey C"
            ),
            mesh=MeshOptions(
                u_cell_size=cell_size[0],
                v_cell_size=cell_size[1],
                w_cell_size=cell_size[2],
                survey_refinement=list(refinement),
                topography_refinement=[0, 0, 1],
                plate_refinement=[1],
                name="mesh C",
            ),
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
        origin = None
        for name in [
            "Gravity Forward",
            "Magnetic Vector Forward",
            "Direct Current 3D Forward",
        ]:
            group = geoh5.get_entity(name)[0]
            mesh = next(child for child in group.children if isinstance(child, Octree))
            survey = next(
                child
                for child in group.children
                if isinstance(child, Points) and not isinstance(child, CurrentElectrode)
            )

            if origin is None:
                origin = mesh.origin
            else:
                mesh.origin = origin

            data = next(k for k in survey.children if "Iteration_0" in k.name)
            orig_data.append(data.values)

            if name == "Gravity Forward":
                params = GravityInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    data_object=survey,
                    gz_channel=data,
                    gz_uncertainty=5e-3,
                    starting_model=0.0,
                    reference_model=0.0,
                    upper_bound=1.0,
                    tile_spatial=2,
                    x_norm=1.1,
                    auto_scale_tiles=True,
                    chi_factor=0.8,
                )
                drivers.append(GravityInversionDriver(params))
            elif name == "Direct Current 3D Forward":
                uncertainties = survey.add_data(
                    {
                        "Uncertainties": {
                            "values": np.abs(data.values) * 0.05 + 1e-4,
                        }
                    }
                )
                params = DC3DInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    data_object=survey,
                    potential_channel=data,
                    model_type="Resistivity (Ohm-m)",
                    potential_uncertainty=uncertainties,
                    tile_spatial=1,
                    starting_model=100.0,
                    reference_model=100.0,
                    save_sensitivities=True,
                    solver_type="Mumps",
                )
                drivers.append(DC3DInversionDriver(params))
            else:
                params = MagneticVectorInversionOptions.build(
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
                    tmi_channel=data,
                    tmi_uncertainty=1e1,
                    tile_spatial=2,
                    auto_scale_tiles=False,
                )
                drivers.append(MagneticVectorInversionDriver(params))

        # Run the inverse
        joint_params = JointCrossGradientOptions.build(
            geoh5=geoh5,
            topography_object=topography,
            group_a=drivers[0].out_group,
            group_a_multiplier=1.0,
            group_b=drivers[1].out_group,
            group_b_multiplier=1.0,
            group_c=drivers[2].out_group,
            group_c_multiplier=1.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-1,
            cross_gradient_weight_a_b=1e0,
            cross_gradient_weight_c_a=1e0,
            cross_gradient_weight_c_b=1e0,
            percentile=100,
        )
    file = joint_params.write_ui_json(tmp_path / "Joint_Inv_run.ui.json")
    driver = JointCrossGradientDriver.start(file)
    driver.run()

    # Check that the norm applied to the sub-driver is maintained
    irls_directive = next(
        directive
        for directive in driver.directives
        if isinstance(directive, UpdateIRLS)
    )
    np.testing.assert_almost_equal(irls_directive.metrics.input_norms[0][1], 1.1)

    if not pytest:
        return
    # Mix of scaling on misfits and tiles.
    # Expecting that gravity tiles are independently scaled, but MagneticVector tiles take
    # the scaling from its total misfit.
    np.testing.assert_allclose(
        driver.directives.scale_misfits.scalings,
        [1, 0.7558, 0.5, 0.5, 0.6710],
        atol=1e-3,
    )
    # Check that scaling * chi factor is reflected in data misfit multipliers
    np.testing.assert_allclose(
        driver.data_misfit.multipliers,
        [0.8, 0.6046, 0.5, 0.5, 0.6710],
        atol=1e-3,
    )

    with Workspace(driver.params.geoh5.h5file):
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )

        output["data"] = np.hstack(orig_data)
        if pytest:
            check_target(output, target_run)


def test_joint_cross_gradient_rotated_run(
    tmp_path,
    caplog,
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
        origin = None
        for name in [
            "Direct Current 3D Forward",
            "Magnetic Vector Forward",
        ]:
            group = geoh5.get_entity(name)[0]
            mesh = next(child for child in group.children if isinstance(child, Octree))
            survey = next(
                child
                for child in group.children
                if isinstance(child, Points) and not isinstance(child, CurrentElectrode)
            )

            if origin is None:
                origin = mesh.origin
            else:
                mesh.origin = origin

            dip, direction = mesh.add_data(
                {
                    "dip": {"values": np.full(mesh.n_cells, 45.0)},
                    "direction": {"values": np.full(mesh.n_cells, 90.0)},
                }
            )
            gradient_rotation = PropertyGroup(
                name="gradient_rotations",
                property_group_type=GroupTypeEnum.DIPDIR,
                properties=[direction, dip],
                parent=mesh,
            )

            data = next(k for k in survey.children if "Iteration_0" in k.name)
            orig_data.append(data.values)

            if name == "Direct Current 3D Forward":
                uncertainties = survey.add_data(
                    {
                        "Uncertainties": {
                            "values": np.abs(data.values) * 0.05 + 1e-4,
                        }
                    }
                )
                params = DC3DInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    alpha_s=1.0,
                    topography_object=topography,
                    data_object=survey,
                    potential_channel=data,
                    model_type="Resistivity (Ohm-m)",
                    potential_uncertainty=uncertainties,
                    tile_spatial=1,
                    starting_model=100.0,
                    reference_model=100.0,
                    gradient_rotation=gradient_rotation,
                    save_sensitivities=True,
                    solver_type="Mumps",
                )
                drivers.append(DC3DInversionDriver(params))
            else:
                params = MagneticVectorPDEInversionOptions.build(
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
                    tmi_channel=data,
                    tmi_uncertainty=1e1,
                    tile_spatial=2,
                    auto_scale_tiles=False,
                )
                drivers.append(MagneticVectorPDEInversionDriver(params))

        # Run the inverse
        joint_params = JointCrossGradientOptions.build(
            geoh5=geoh5,
            topography_object=topography,
            group_a=drivers[0].out_group,
            group_a_multiplier=1.0,
            group_b=drivers[1].out_group,
            group_b_multiplier=1.0,
        )

    with caplog.at_level(logging.WARNING):
        _ = JointCrossGradientDriver(joint_params)

    assert "Some drivers do not have a model" in caplog.text

    # Add gradient rotation to the mvi driver and check it is used
    params.models.gradient_rotation = gradient_rotation
    params.out_group = None
    drivers[-1] = MagneticVectorPDEInversionDriver(params)
    # Run the inverse
    joint_params = JointCrossGradientOptions.build(
        geoh5=geoh5,
        topography_object=topography,
        group_a=drivers[0].out_group,
        group_a_multiplier=1.0,
        group_b=drivers[1].out_group,
        group_b_multiplier=1.0,
        max_global_iterations=max_iterations,
    )
    joint_driver = JointCrossGradientDriver(joint_params)
    assert joint_driver.models.gradient_dip is not None

    joint_driver.run()


if __name__ == "__main__":
    # Full run
    test_joint_cross_gradient_fwr_run(
        Path("./"),
        n_grid_points=16,
        n_lines=5,
        cell_size=(10.0, 10.0, 10.0),
        refinement=(4, 4),
    )
    test_joint_cross_gradient_inv_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
