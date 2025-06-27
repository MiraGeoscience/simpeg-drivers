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
from unittest.mock import patch

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.groups.property_group import PropertyGroup
from geoh5py.workspace import Workspace
from pytest import raises

from simpeg_drivers.electricals.direct_current.two_dimensions.driver import (
    DC2DForwardDriver,
    DC2DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.options import (
    DC2DForwardOptions,
    DC2DInversionOptions,
)
from simpeg_drivers.options import (
    ActiveCellsOptions,
    DrapeModelOptions,
    LineSelectionOptions,
)
from simpeg_drivers.utils.utils import get_inversion_output
from tests.testing_utils import check_target, setup_inversion_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.6345768240307744, "phi_d": 1090, "phi_m": 3.99}


def test_dc2d_rotated_grad_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
    refinement=(4, 6),
):
    plate_model = PlateModel(
        strike_length=1000.0,
        dip_length=150.0,
        width=20.0,
        origin=(50.0, 0.0, -30),
        direction=90,
        dip=45,
    )

    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        plate_model=plate_model,
        background=0.01,
        anomaly=10.0,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        inversion_type="direct current 2d",
        drape_height=0.0,
        flatten=False,
    )
    line_selection = LineSelectionOptions(
        line_object=geoh5.get_entity("line_ids")[0],
        line_id=101,
    )
    params = DC2DForwardOptions.build(
        geoh5=geoh5,
        data_object=survey,
        line_selection=line_selection,
        drape_model=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=100.0,
            horizontal_padding=100.0,
            vertical_padding=100.0,
            expansion_factor=1.1,
        ),
        starting_model=model,
        topography_object=topography,
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
        potential = geoh5.get_entity("Iteration_0_dc")[0]
        topography = geoh5.get_entity("topography")[0]

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
            topography_object=topography,
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
            z_norm=0.0,
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
