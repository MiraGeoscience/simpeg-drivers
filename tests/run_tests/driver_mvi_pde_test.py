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
from dask.distributed import LocalCluster, performance_report
from geoh5py.groups import PropertyGroup
from geoh5py.groups.property_group import GroupTypeEnum
from geoh5py.objects import Curve
from geoh5py.workspace import Workspace

from simpeg_drivers.potential_fields.magnetic_vector_pde import (
    MagneticVectorPDEForwardDriver,
    MagneticVectorPDEForwardOptions,
    MagneticVectorPDEInversionDriver,
    MagneticVectorPDEInversionOptions,
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

target_mvi_pde_run = {"data_norm": 181.99122096291276, "phi_d": 408, "phi_m": 0.013}


def test_mvi_pde_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    cell_size=(5.0, 5.0, 5.0),
    refinement=(2,),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="magnetic_vector_pde",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=5.0
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
        ),
        model=ModelOptions(anomaly=0.05),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        inducing_field = (50000.0, 90.0, 0.0)
        params = MagneticVectorPDEForwardOptions.build(
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
    fwr_driver = MagneticVectorPDEForwardDriver(params)
    fwr_driver.run()


def test_mvi_pde_run(
    tmp_path: Path,
    max_iterations=5,
    upper_bound=1e-2,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_mvi_pde_fwr_run0" / "inversion_test.ui.geoh5"

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
        params = MagneticVectorPDEInversionOptions.build(
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
            upper_bound=upper_bound,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-0,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = MagneticVectorPDEInversionDriver(params)
    driver.run()

    if pytest:
        with Workspace(driver.params.geoh5.h5file):
            # Re-open the workspace and get iterations
            output = get_inversion_output(
                driver.params.geoh5.h5file, driver.params.out_group.uid
            )
            output["data"] = orig_tmi
            check_target(output, target_mvi_pde_run)


if __name__ == "__main__":
    # Full run
    with LocalCluster(processes=True, n_workers=2, threads_per_worker=6) as cluster:
        with cluster.get_client():
            # Full run
            with performance_report(filename="diagnostics.html"):
                test_mvi_pde_fwr_run(
                    Path("./"),
                    n_grid_points=20,
                    cell_size=(5.0, 5.0, 5.0),
                    refinement=(4, 4),
                )
                test_mvi_pde_run(Path("./"), max_iterations=30, pytest=False)
