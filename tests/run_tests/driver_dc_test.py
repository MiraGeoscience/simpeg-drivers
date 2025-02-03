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
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.three_dimensions.driver import (
    DirectCurrent3DForwardDriver,
    DirectCurrent3DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.params import (
    DirectCurrent3DForwardParams,
    DirectCurrent3DInversionParams,
)
from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.15043, "phi_d": 221.4, "phi_m": 358.6}


def test_dc_3d_fwr_run(
    tmp_path: Path,
    n_electrodes=4,
    n_lines=3,
    refinement=(4, 6),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.01,
        anomaly=10,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        drape_height=0.0,
        inversion_type="dcip",
        flatten=False,
    )

    # Randomly flip order of receivers
    old = np.random.randint(0, survey.cells.shape[0], n_electrodes)
    indices = np.ones(survey.cells.shape[0], dtype=bool)
    indices[old] = False

    tx_id = np.r_[survey.ab_cell_id.values[indices], survey.ab_cell_id.values[~indices]]
    cells = np.vstack([survey.cells[indices, :], survey.cells[~indices, :]])

    survey.ab_cell_id = tx_id
    survey.cells = cells

    geoh5.close()

    active_cells = ActiveCellsData(topography_object=topography)
    params = DirectCurrent3DForwardParams(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=active_cells,
        z_from_topo=False,
        data_object=survey,
        starting_model=model,
        resolution=None,
    )
    fwr_driver = DirectCurrent3DForwardDriver(params)
    fwr_driver.run()


def test_dc_3d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
    n_lines=3,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_dc_3d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_dc")[0]
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        active_cells = ActiveCellsData(topography_object=topography)
        params = DirectCurrent3DInversionParams(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=active_cells,
            data_object=potential.parent,
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            z_from_topo=False,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            prctile=100,
            upper_bound=10,
            tile_spatial=n_lines,
            store_sensitivities="ram",
            auto_scale_misfits=False,
            save_sensitivities=True,
            coolingRate=1,
            chi_factor=0.5,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DirectCurrent3DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))
    # Should not be auto-scaling
    np.testing.assert_allclose(driver.data_misfit.multipliers, [1, 1, 1])
    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)

    with Workspace(workpath) as geoh5:
        assert geoh5.get_entity("Iteration_1_sensitivities")[0] is not None


def test_dc_single_line_fwr_run(
    tmp_path: Path,
    n_electrodes=4,
    n_lines=1,
    refinement=(4, 6),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.01,
        anomaly=10,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        drape_height=0.0,
        inversion_type="dcip",
        flatten=False,
    )
    active_cells = ActiveCellsData(topography_object=topography)
    params = DirectCurrent3DForwardParams(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=active_cells,
        z_from_topo=False,
        data_object=survey,
        starting_model=model,
        resolution=None,
    )

    fwr_driver = DirectCurrent3DForwardDriver(params)
    assert np.all(fwr_driver.window.window["size"] > 0)


if __name__ == "__main__":
    # Full run

    test_dc_3d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=5,
        refinement=(4, 8),
    )

    test_dc_3d_run(
        Path("./"),
        n_lines=5,
        max_iterations=15,
        pytest=False,
    )
