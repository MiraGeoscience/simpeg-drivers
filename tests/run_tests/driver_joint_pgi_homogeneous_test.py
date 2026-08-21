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
import pytest
from geoapps_utils import GeoAppsError
from geoapps_utils.modelling.plates import PlateModel, make_plate
from geoh5py.groups.property_group import GroupTypeEnum, PropertyGroup
from geoh5py.objects import Octree, Points
from geoh5py.workspace import Workspace

from simpeg_drivers.joint.joint_petrophysics.driver import JointPetrophysicsDriver
from simpeg_drivers.joint.joint_petrophysics.options import JointPetrophysicsOptions
from simpeg_drivers.potential_fields.gravity.forward import (
    GravityForwardDriver,
    GravityForwardOptions,
)
from simpeg_drivers.potential_fields.gravity.inversion import (
    GravityInversionDriver,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_scalar.inversion import (
    MagneticInversionDriver,
    MagneticInversionOptions,
)
from simpeg_drivers.potential_fields.magnetic_vector.forward import (
    MagneticVectorForwardDriver,
    MagneticVectorForwardOptions,
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

target_run = {"data_norm": 422.92317507375105, "phi_d": 2920, "phi_m": 417}
INDUCING_FIELD = (50000.0, 90.0, 0.0)


def test_homogeneous_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    cell_size=(20.0, 20.0, 20.0),
    refinement=(2,),
):
    # Create local problem A
    opts = SyntheticsComponentsOptions(
        method="gravity",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points,
            n_lines=n_grid_points,
            drape=15.0,
            name="survey A",
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
        model=ModelOptions(
            anomaly=0.75,
            name="model A",
            plate=PlateModel(
                easting=-60,
                strike_length=30.0,
                dip_length=30.0,
                width=30.0,
                northing=0.0,
                elevation=20.0,
                dip=90.0,
                direction=0.0,
            ),
        ),
        active=SyntheticsActiveCellsOptions(name="active A"),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        # Change half the model
        ind = components.mesh.centroids[:, 0] > -2
        components.model.values[ind] = 0.05

        # Add a block
        components.model.values = make_plate(
            points=components.mesh.centroids,
            plate=PlateModel(
                strike_length=30.0,
                dip_length=30.0,
                width=30.0,
                easting=40.0,
                northing=0.0,
                elevation=20.0,
                dip=90.0,
                direction=0.0,
            ),
            background=components.model.values,
            anomaly=-0.5,
        )

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
            model=ModelOptions(
                anomaly=0.025,
                name="model B",
                plate=PlateModel(
                    easting=-60,
                    strike_length=30.0,
                    dip_length=30.0,
                    width=30.0,
                    northing=0.0,
                    elevation=20.0,
                    dip=90.0,
                    direction=0.0,
                ),
            ),
            active=SyntheticsActiveCellsOptions(name="active B"),
        )
        components = SyntheticsComponents(geoh5, options=opts)
        # Change half the model
        ind = components.mesh.centroids[:, 0] > -2
        components.model.values[ind] = 0.01

        # Add a block
        components.model.values = make_plate(
            points=components.mesh.centroids,
            plate=PlateModel(
                strike_length=30.0,
                dip_length=30.0,
                width=30.0,
                easting=40.0,
                northing=0.0,
                elevation=20.0,
                dip=90.0,
                direction=0.0,
            ),
            background=components.model.values,
            anomaly=0.05,
        )

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

    fwr_driver_a.run()
    fwr_driver_b.run()


def test_homogeneous_run(
    tmp_path: Path,
    max_iterations=1,
    use_pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if use_pytest:
        workpath = (
            tmp_path.parent / "test_homogeneous_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath, mode="r+") as geoh5:
        topography = geoh5.get_entity("topography")[0]
        drivers = []
        orig_data = []
        petrophysics = None
        gradient_rotation = None

        for name in ["Gravity Forward", "Magnetic Forward"]:
            group = geoh5.get_entity(name)[0]
            mesh = next(child for child in group.children if isinstance(child, Octree))
            survey = next(
                child for child in group.children if isinstance(child, Points)
            )

            if name == "Gravity Forward":
                global_mesh = mesh.copy(parent=geoh5)
                model = global_mesh.get_entity("starting_model")[0]

                mapping = {}
                vals = np.zeros_like(model.values, dtype=int)
                model_values = np.round(model.values, decimals=4)
                for ind, value in enumerate(np.unique(model_values)):
                    mapping[ind + 1] = f"Unit{ind}"
                    vals[model_values == value] = ind + 1

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

            data = next(k for k in survey.children if "Iteration_0" in k.name)
            orig_data.append(data.values)

            ref_model = mesh.get_entity("starting_model")[0].copy(name="ref_model")
            ref_model.values = ref_model.values / 2.0

            if name == "Gravity Forward":
                params = GravityInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    topography_object=topography,
                    data_object=survey,
                    gz_channel=data,
                    gz_uncertainty=5e-3,
                    starting_model=ref_model,
                    reference_model=ref_model,
                )
                driver = GravityInversionDriver(params)

                # Remove inversion type as per current json on file
                options = driver.out_group.options
                options.pop("inversion_type", None)
                driver.out_group.options = options
                drivers.append(driver)
            else:
                params = MagneticInversionOptions.build(
                    geoh5=geoh5,
                    mesh=mesh,
                    topography_object=topography,
                    inducing_field_strength=INDUCING_FIELD[0],
                    inducing_field_inclination=INDUCING_FIELD[1],
                    inducing_field_declination=INDUCING_FIELD[2],
                    data_object=survey,
                    starting_model=ref_model,
                    reference_model=None,
                    tile_spatial=1,
                    tmi_channel=data,
                    tmi_uncertainty=5e0,
                )
                drivers.append(MagneticInversionDriver(params))

            if len(drivers) == 1:
                # Test if single group is valid
                params = JointPetrophysicsOptions.build(
                    topography_object=topography,
                    geoh5=geoh5,
                    group_a=drivers[0].out_group,
                    mesh=global_mesh,
                    petrophysical_model=petrophysics,
                )
                driver = JointPetrophysicsDriver(params)
                assert len(driver.data_misfit.objfcts) == 1
                assert driver.data_misfit.multipliers == [1.0]

        # Re-build full
        joint_params = JointPetrophysicsOptions.build(
            topography_object=topography,
            geoh5=geoh5,
            group_a=drivers[0].out_group,
            group_a_multiplier=1.0,
            group_b=drivers[1].out_group,
            group_b_multiplier=1.0,
            mesh=global_mesh,
            gradient_rotation=gradient_rotation,
            alpha_s=10.0,
            length_scale_x=1.0,
            length_scale_y=1.0,
            length_scale_z=1.0,
            petrophysical_model=petrophysics,
            initial_beta_ratio=1e2,
            max_global_iterations=max_iterations,
            max_irls_iterations=1,
        )
        driver = JointPetrophysicsDriver(joint_params)
        driver.initialize()
        with pytest.raises(
            GeoAppsError, match="A reference model must be set and active on each"
        ):
            _ = driver.means

        # Re-instate
        params.models.reference_model = ref_model
        params.out_group = None
        new_driver = MagneticInversionDriver(params)
        joint_params.group_b = new_driver.out_group
        driver = JointPetrophysicsDriver(joint_params)

        driver.run()

    if use_pytest:
        assert driver.regularization.objfcts[-1].gmm.fixed_membership[0, 1] == 1

        with Workspace(driver.params.geoh5.h5file) as run_ws:
            output = get_inversion_output(
                driver.params.geoh5.h5file, driver.out_group.uid
            )
            output["data"] = np.hstack(orig_data)
            check_target(output, target_run)

            out_group = run_ws.get_entity(driver.out_group.uid)[0]
            mesh = out_group.get_entity("mesh A")[0]
            petro_model = mesh.get_entity("petrophysical_model")[0]
            assert len(np.unique(petro_model.values)) == 5


if __name__ == "__main__":
    # Full run
    test_homogeneous_fwr_run(
        Path("./"),
        n_grid_points=20,
        cell_size=(10.0, 10.0, 10.0),
        refinement=(6, 4),
    )

    test_homogeneous_run(
        Path("./"),
        max_iterations=20,
        use_pytest=False,
    )
