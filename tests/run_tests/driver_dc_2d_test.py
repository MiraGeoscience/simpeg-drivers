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
from geoh5py.data import ReferencedData
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.two_dimensions.driver import (
    DC2DForwardDriver,
    DC2DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.params import (
    DC2DForwardOptions,
    DC2DInversionOptions,
)
from simpeg_drivers.electricals.params import DrapeModelOptions, LineSelectionOptions
from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {
    "data_norm": 0.59563,
    "phi_d": 2814,
    "phi_m": 15.88,
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
    line_selection = LineSelectionOptions(
        line_object=geoh5.get_entity("line_ids")[0],
        line_id=101,
    )
    params = DC2DForwardOptions(
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
        active_cells=ActiveCellsOptions(topography_object=topography),
    )

    fwr_driver = DC2DForwardDriver(params)
    fwr_driver.run()


def test_dc_2d_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_dc_2d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_dc")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = DC2DInversionOptions(
            geoh5=geoh5,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=100.0,
                horizontal_padding=100.0,
                vertical_padding=100.0,
                expansion_factor=1.1,
            ),
            active_cells=ActiveCellsOptions(topography_object=topography),
            line_selection=LineSelectionOptions(
                line_object=geoh5.get_entity("line_ids")[0],
                line_id=101,
            ),
            data_object=potential.parent,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            model_type="Resistivity (Ohm-m)",
            starting_model=100.0,
            reference_model=100.0,
            s_norm=0.0,
            x_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            potential_channel_bool=True,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            prctile=100,
            lower_bound=0.1,
            coolingRate=1,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

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
