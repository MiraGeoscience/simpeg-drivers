# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import numpy as np
from geoh5py.objects import Octree
from geoh5py.workspace import Workspace
from simpeg.directives import SavePropertyGroup

from simpeg_drivers.electricals.direct_current.three_dimensions.driver import (
    DC3DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.options import (
    DC3DInversionOptions,
)
from simpeg_drivers.electromagnetics.time_domain.driver import TDEMInversionDriver
from simpeg_drivers.electromagnetics.time_domain.options import TDEMInversionOptions
from simpeg_drivers.joint.joint_surveys import JointSurveysOptions
from simpeg_drivers.joint.joint_surveys.driver import JointSurveyDriver
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import GravityInversionDriver
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

target_run = {"data_norm": 0.2997791660779469, "phi_d": 398, "phi_m": 102}


def test_joint_surveys_fwr_run(
    tmp_path,
    n_grid_points=6,
    refinement=(2,),
):
    # Create local problem A
    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0, name="survey A"
        ),
        mesh=MeshOptions(refinement=refinement, name="mesh A"),
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
    fwr_driver_a = GravityInversionDriver(params)

    with fwr_driver_a.out_group.workspace.open():
        fwr_driver_a.out_group.name = "Gravity Forward [0]"

    # Create local problem B
    with geoh5.open():
        opts = SyntheticsComponentsOptions(
            method="gravity",
            survey=SurveyOptions(
                n_stations=int(n_grid_points / 2),
                n_lines=int(n_grid_points / 2),
                drape=10.0,
                name="survey B",
            ),
            mesh=MeshOptions(refinement=(0, 2), name="mesh B"),
            model=ModelOptions(anomaly=0.75, name="model B"),
            active=SyntheticsActiveCellsOptions(name="active B"),
        )
        components = SyntheticsComponents(geoh5, options=opts)
        params = GravityForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver_b = GravityInversionDriver(params)

    with fwr_driver_b.out_group.workspace.open():
        # Force co-location of meshes
        fwr_driver_b.inversion_mesh.entity.origin = (
            fwr_driver_a.inversion_mesh.entity.origin
        )
        fwr_driver_b.out_group.name = "Gravity Forward [1]"
        fwr_driver_b.workspace.update_attribute(
            fwr_driver_b.inversion_mesh.entity, "attributes"
        )
        fwr_driver_b.inversion_mesh._mesh = None  # pylint: disable=protected-access
    fwr_driver_a.run()
    fwr_driver_b.run()


def test_joint_surveys_inv_run(
    tmp_path,
    max_iterations=1,
    unittest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if unittest:
        workpath = (
            tmp_path.parent / "test_joint_surveys_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        drivers = []
        orig_data = []

        for ind in range(2):
            group = geoh5.get_entity(f"Gravity Forward [{ind}]")[0]
            survey = geoh5.get_entity(group.options["data_object"]["value"])[0]
            mesh = None
            for child in group.children:
                if isinstance(child, Octree):
                    mesh = child
                else:
                    survey = child

            if mesh is None:
                raise ValueError("No mesh found in the group.")

            active_model = mesh.get_entity("active_cells")[0]
            gz = survey.get_data("Iteration_0_gz")[0]
            orig_data.append(gz.values)
            active_cells = ActiveCellsOptions(active_model=active_model)
            params = GravityInversionOptions.build(
                geoh5=geoh5,
                mesh=mesh,
                active_cells=active_cells,
                data_object=survey,
                gz_channel=gz,
                gz_uncertainty=np.var(gz.values) * 2.0,
                starting_model=0.0,
            )
            drivers.append(GravityInversionDriver(params))

        active_model = drivers[0].params.mesh.get_entity("active_cells")[0]
        # Run the inverse
        joint_params = JointSurveysOptions.build(
            geoh5=geoh5,
            active_cells=ActiveCellsOptions(active_model=active_model),
            mesh=drivers[0].params.mesh,
            group_a=drivers[0].out_group,
            group_b=drivers[1].out_group,
            starting_model=1e-4,
            reference_model=0.0,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            lower_bound=0.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-2,
            percentile=100,
        )

    driver = JointSurveyDriver(joint_params)
    driver.run()

    with Workspace(driver.params.geoh5.h5file):
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = np.hstack(orig_data)

        if unittest:
            check_target(output, target_run)


def test_joint_surveys_conductivity_run(
    tmp_path,
):
    opts = SyntheticsComponentsOptions(
        method="direct-current",
        survey=SurveyOptions(n_stations=4, n_lines=4, name="survey A"),
        mesh=MeshOptions(refinement=(2, 2, 2), name="mesh A"),
        model=ModelOptions(anomaly=0.1, background=0.01, name="model A"),
        active=SyntheticsActiveCellsOptions(name="active A"),
    )

    with Workspace.create(tmp_path / f"{__name__}.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        survey = components.survey
        obs, uncrt = survey.add_data(
            {
                "Potentials": {"values": np.random.randn(survey.n_cells)},
                "Uncertainty": {"values": np.ones(survey.n_cells) * 1e-3},
            }
        )
        params = DC3DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            potential_channel=obs,
            potential_uncertainty=uncrt,
            data_object=components.survey,
            starting_model=components.model,
            reference_model=5.0,
            model_type="Resistivity (Ohm-m)",
        )
        driver_A = DC3DInversionDriver(params)
        driver_B = DC3DInversionDriver(params)

        # Run the inverse
        joint_params = JointSurveysOptions.build(
            geoh5=geoh5,
            active_cells=ActiveCellsOptions(topography_object=components.topography),
            mesh=components.mesh,
            group_a=driver_A.out_group,
            group_b=driver_B.out_group,
            starting_model=20.0,
            # Default to Conductivity (S/m)
        )

        driver = JointSurveyDriver(joint_params)
        assert np.isclose(
            driver.models.reference_model[0], np.log(1 / 5.0)
        )  # Took it from driver_A
        assert np.isclose(
            driver.models.starting_model[0], np.log(20.0)
        )  # Took it from joint params


def test_joint_surveys_tem_run(
    tmp_path,
):
    opts = SyntheticsComponentsOptions(
        method="airborne tdem",
        survey=SurveyOptions(n_stations=4, n_lines=4, name="survey A"),
        mesh=MeshOptions(refinement=(2, 2, 2), name="mesh A"),
        model=ModelOptions(anomaly=0.1, background=0.01, name="model A"),
        active=SyntheticsActiveCellsOptions(name="active A"),
    )

    with Workspace.create(tmp_path / f"{__name__}.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        data = {}
        uncertainties = {}
        channels = {
            "z": "dBzdt",
        }
        survey = components.survey
        for cname in channels.values():
            data[cname] = []
            uncertainties[f"{cname} uncertainties"] = []
            for ii, _ in enumerate(components.survey.channels):
                data_entity, uncert = survey.add_data(
                    {
                        f"{cname}_[{ii}]": {
                            "values": np.random.randn(survey.n_vertices)
                        },
                        f"{cname}_unc[{ii}]": {
                            "values": np.ones(survey.n_vertices) * 1e-3
                        },
                    }
                )
                data[cname].append(data_entity)
                uncertainties[f"{cname} uncertainties"].append(uncert)

        components.survey.add_components_data(data)
        components.survey.add_components_data(uncertainties)

        data_kwargs = {}
        for chan in channels:
            data_kwargs[f"{chan}_channel"] = components.survey.fetch_property_group(
                name=f"dB{chan}dt"
            )
            data_kwargs[f"{chan}_uncertainty"] = components.survey.fetch_property_group(
                name=f"dB{chan}dt uncertainties"
            )

        # Run the inverse
        params = TDEMInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=1e-3,
            **data_kwargs,
        )
        driver_A = TDEMInversionDriver(params)
        driver_B = TDEMInversionDriver(params)

        # Run the inverse
        joint_params = JointSurveysOptions.build(
            geoh5=geoh5,
            active_cells=ActiveCellsOptions(topography_object=components.topography),
            mesh=components.mesh,
            group_a=driver_A.out_group,
            group_b=driver_B.out_group,
            starting_model=1e-3,
        )

        driver = JointSurveyDriver(joint_params)
        assert (
            len(
                [
                    group
                    for group in driver.directives.directive_list
                    if isinstance(group, SavePropertyGroup)
                ]
            )
            == 5
        )


if __name__ == "__main__":
    # Full run
    test_joint_surveys_fwr_run(
        Path("./"),
        n_grid_points=20,
        refinement=(4, 4),
    )
    test_joint_surveys_inv_run(
        Path("./"),
        max_iterations=20,
        unittest=False,
    )
