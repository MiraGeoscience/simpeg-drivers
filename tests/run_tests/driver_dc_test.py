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

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DirectCurrent3DParams,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.driver import (
    DirectCurrent3DDriver,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output

# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.15258, "phi_d": 31.85, "phi_m": 122.7}


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

    params = DirectCurrent3DParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
        resolution=None,
    )
    params.workpath = tmp_path
    fwr_driver = DirectCurrent3DDriver(params)
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
        params = DirectCurrent3DParams(
            geoh5=geoh5,
            mesh=mesh.uid,
            topography_object=topography.uid,
            data_object=potential.parent.uid,
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            potential_channel_bool=True,
            z_from_topo=False,
            potential_channel=potential.uid,
            potential_uncertainty=1e-3,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            prctile=100,
            upper_bound=10,
            tile_spatial=n_lines,
            store_sensitivities="ram",
            coolingRate=1,
            chi_factor=0.5,
        )
        params.write_input_file(path=tmp_path, name="Inv_run")

    driver = DirectCurrent3DDriver.start(str(tmp_path / "Inv_run.ui.json"))

    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


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
    params = DirectCurrent3DParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
        resolution=None,
    )
    params.workpath = tmp_path
    fwr_driver = DirectCurrent3DDriver(params)
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
