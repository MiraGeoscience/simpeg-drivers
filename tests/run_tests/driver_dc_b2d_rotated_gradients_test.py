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

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.driver import (
    DCBatch2DForwardDriver,
    DCBatch2DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.options import (
    DCBatch2DForwardOptions,
    DCBatch2DInversionOptions,
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

target_run = {"data_norm": 1.1038993594022803, "phi_d": 308, "phi_m": 0.0237}


def test_dc_rotated_p3d_fwr_run(
    tmp_path: Path, n_electrodes=10, n_lines=3, refinement=(4, 6)
):
    plate_model = PlateModel(
        strike_length=1000.0,
        dip_length=150.0,
        width=20.0,
        origin=(0.0, 0.0, -50),
        direction=90,
        dip=45,
    )

    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        plate_model=plate_model,
        background=0.01,
        anomaly=10.0,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        inversion_type="direct current pseudo 3d",
        drape_height=0.0,
        flatten=False,
    )
    params = DCBatch2DForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        drape_model=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=100.0,
            expansion_factor=1.1,
            horizontal_padding=1000.0,
            vertical_padding=1000.0,
        ),
        active_cells=ActiveCellsOptions(topography_object=topography),
        data_object=survey,
        starting_model=model,
        line_selection=LineSelectionOptions(
            line_object=geoh5.get_entity("line_ids")[0]
        ),
    )
    fwr_driver = DCBatch2DForwardDriver(params)
    fwr_driver.run()


def test_dc_rotated_gradient_p3d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_dc_rotated_p3d_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_dc")[0]
        out_group = geoh5.get_entity("Line 1")[0].parent
        mesh = out_group.get_entity("mesh")[0]  # Finds the octree mesh
        topography = geoh5.get_entity("topography")[0]

        # Create property group with orientation
        dip = np.ones(mesh.n_cells) * 45
        azimuth = np.ones(mesh.n_cells) * 90

        data_list = mesh.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            mesh, properties=data_list, property_group_type="Dip direction & dip"
        )

        # Run the inverse
        params = DCBatch2DInversionOptions(
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
            active_cells=ActiveCellsOptions(topography_object=topography),
            data_object=potential.parent,
            gradient_rotation=pg,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            line_selection=LineSelectionOptions(
                line_object=geoh5.get_entity("line_ids")[0]
            ),
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            gradient_type="components",
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            cooling_rate=1,
            file_control=FileControlOptions(cleanup=False),
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DCBatch2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

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
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_dc_rotated_p3d_fwr_run(
        Path("./"), n_electrodes=20, n_lines=3, refinement=(4, 8)
    )
    test_dc_rotated_gradient_p3d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
