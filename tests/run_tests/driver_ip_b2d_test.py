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

import json
from pathlib import Path

from geoh5py.groups import SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.driver import (
    IPBatch2DForwardDriver,
    IPBatch2DInversionDriver,
)
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.options import (
    IPBatch2DForwardOptions,
    IPBatch2DInversionOptions,
)
from simpeg_drivers.electricals.options import (
    FileControlOptions,
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

target_run = {"data_norm": 0.0919313, "phi_d": 25600, "phi_m": 0.201}


def test_ip_p3d_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
    refinement=(4, 6),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=1e-6,
        anomaly=1e-1,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        inversion_type="induced polarization pseudo 3d",
        drape_height=0.0,
        flatten=False,
    )

    params = IPBatch2DForwardOptions.build(
        geoh5=geoh5,
        mesh=model.parent,
        drape_model=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=100.0,
            expansion_factor=1.1,
            horizontal_padding=100.0,
            vertical_padding=100.0,
        ),
        active_cells=ActiveCellsOptions(
            topography_object=topography,
        ),
        data_object=survey,
        conductivity_model=1e-2,
        starting_model=model,
        line_selection=LineSelectionOptions(
            line_object=geoh5.get_entity("line_ids")[0]
        ),
    )

    fwr_driver = IPBatch2DForwardDriver(params)
    fwr_driver.run()


def test_ip_p3d_run(
    tmp_path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_ip_p3d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        chargeability = geoh5.get_entity("Iteration_0_ip")[0]
        out_group = geoh5.get_entity("Line 1")[0].parent
        mesh = out_group.get_entity("mesh")[0]  # Finds the octree mesh
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = IPBatch2DInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=100.0,
                expansion_factor=1.1,
                horizontal_padding=1000.0,
                vertical_padding=1000.0,
            ),
            topography_object=topography,
            data_object=chargeability.parent,
            chargeability_channel=chargeability,
            chargeability_uncertainty=2e-4,
            line_selection=LineSelectionOptions(
                line_object=geoh5.get_entity("line_ids")[0],
            ),
            conductivity_model=1e-2,
            starting_model=1e-6,
            reference_model=1e-6,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            length_scale_x=1.0,
            length_scale_z=1.0,
            gradient_type="components",
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            percentile=100,
            upper_bound=0.1,
            cooling_rate=1,
            file_control=FileControlOptions(cleanup=False),
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = IPBatch2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    basepath = workpath.parent
    with open(basepath / "lookup.json", encoding="utf8") as f:
        lookup = json.load(f)
        middle_line_id = next(k for k, v in lookup.items() if v["line_id"] == 101)

    with Workspace(basepath / f"{middle_line_id}.ui.geoh5", mode="r") as workspace:
        middle_inversion_group = next(
            k for k in workspace.groups if isinstance(k, SimPEGGroup)
        )
        filedata = middle_inversion_group.get_entity("SimPEG.out")[0]

        with driver.batch2d_params.out_group.workspace.open(mode="r+"):
            filedata.copy(parent=driver.batch2d_params.out_group)

    output = get_inversion_output(
        driver.batch2d_params.geoh5.h5file, driver.batch2d_params.out_group.uid
    )
    if geoh5.open():
        output["data"] = chargeability.values
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_ip_p3d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=3,
        refinement=(4, 8),
    )
    test_ip_p3d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
