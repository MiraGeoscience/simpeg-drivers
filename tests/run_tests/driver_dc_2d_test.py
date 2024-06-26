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

from simpeg_drivers.electricals.direct_current.two_dimensions.driver import (
    DirectCurrent2DDriver,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.params import (
    DirectCurrent2DParams,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output

# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {
    "data_norm": 0.59563,
    "phi_d": 1400,
    "phi_m": 8.004,
}


def test_dc_2d_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
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
        inversion_type="dcip_2d",
        drape_height=0.0,
        flatten=False,
    )
    params = DirectCurrent2DParams(
        forward_only=True,
        geoh5=geoh5,
        u_cell_size=5.0,
        v_cell_size=5.0,
        depth_core=100.0,
        horizontal_padding=100.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
        topography_object=topography.uid,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
        line_object=geoh5.get_entity("line_ids")[0].uid,
        line_id=101,
    )
    params.workpath = tmp_path
    fwr_driver = DirectCurrent2DDriver(params)
    fwr_driver.run()


def test_dc_2d_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_dc_2d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_dc")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = DirectCurrent2DParams(
            geoh5=geoh5,
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=100.0,
            horizontal_padding=100.0,
            vertical_padding=100.0,
            expansion_factor=1.1,
            topography_object=topography.uid,
            data_object=potential.parent.uid,
            potential_channel=potential.uid,
            potential_uncertainty=1e-3,
            line_object=geoh5.get_entity("line_ids")[0].uid,
            line_id=101,
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            potential_channel_bool=True,
            z_from_topo=True,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            prctile=100,
            upper_bound=10,
            coolingRate=1,
        )
        params.write_input_file(path=tmp_path, name="Inv_run")

    driver = DirectCurrent2DDriver.start(str(tmp_path / "Inv_run.ui.json"))

    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values[np.isfinite(potential.values)]
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_dc_2d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=3,
        refinement=(4, 8),
    )
    test_dc_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
