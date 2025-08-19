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
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups.property_group import PropertyGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.two_dimensions.driver import (
    DC2DForwardDriver,
    DC2DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.options import (
    DC2DForwardOptions,
    DC2DInversionOptions,
)
from simpeg_drivers.options import (
    DrapeModelOptions,
    LineSelectionOptions,
)
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
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

target_run = {"data_norm": 0.63464358755296, "phi_d": 1100, "phi_m": 5.04}


def test_dc2d_rotated_grad_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
    refinement=(4, 6),
):
    filepath = Path(tmp_path) / "inversion_test.ui.geoh5"
    with Workspace.create(filepath) as geoh5:
        # Run the forward
        components = SyntheticsComponents(
            geoh5=geoh5,
            options=SyntheticsComponentsOptions(
                method="direct current 2d",
                survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
                mesh=MeshOptions(refinement=refinement),
                model=ModelOptions(
                    background=0.01,
                    anomaly=10.0,
                    plate=PlateModel(
                        strike_length=1000.0,
                        dip_length=150.0,
                        width=20.0,
                        origin=(50.0, 0.0, -30),
                        direction=90,
                        dip=45,
                    ),
                ),
            ),
        )

        line_selection = LineSelectionOptions(
            line_object=components.survey.get_data("line_ids")[0],
            line_id=101,
        )
        params = DC2DForwardOptions.build(
            geoh5=geoh5,
            data_object=components.survey,
            line_selection=line_selection,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=100.0,
                horizontal_padding=100.0,
                vertical_padding=100.0,
                expansion_factor=1.1,
            ),
            starting_model=components.model,
            topography_object=components.topography,
        )
    fwr_driver = DC2DForwardDriver(params)
    fwr_driver.run()


def test_dc2d_rotated_grad_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_dc2d_rotated_grad_fwr_run0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_potential")[0]
        components = SyntheticsComponents(geoh5)

        orig_potential = potential.values.copy()
        mesh = geoh5.get_entity("Models")[0]

        # Create property group with orientation
        i = np.ones(mesh.n_cells)
        j = np.zeros(mesh.n_cells)
        k = np.ones(mesh.n_cells)

        data_list = mesh.add_data(
            {
                "i": {"values": i},
                "j": {"values": j},
                "k": {"values": k},
            }
        )
        pg = PropertyGroup(mesh, properties=data_list, property_group_type="3D vector")

        # Run the inverse
        params = DC2DInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=100.0,
                horizontal_padding=100.0,
                vertical_padding=100.0,
                expansion_factor=1.1,
            ),
            topography_object=components.topography,
            line_selection=LineSelectionOptions(
                line_object=geoh5.get_entity("line_ids")[0],
                line_id=101,
            ),
            data_object=potential.parent,
            gradient_rotation=pg,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            model_type="Resistivity (Ohm-m)",
            starting_model=100.0,
            reference_model=100.0,
            s_norm=1.0,
            x_norm=0.0,
            z_norm=2.0,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            percentile=100,
            lower_bound=0.1,
            cooling_rate=1,
            starting_chi_factor=1.0,
            chi_factor=0.1,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with Workspace(driver.params.geoh5.h5file) as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_potential

        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_dc2d_rotated_grad_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=3,
        refinement=(4, 8),
    )

    test_dc2d_rotated_grad_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
