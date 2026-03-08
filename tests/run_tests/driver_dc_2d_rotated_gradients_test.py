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

import json
from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups import PropertyGroup, SimPEGGroup
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
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 1.1067294238524659, "phi_d": 55.6, "phi_m": 7.08}


def test_dc_rotated_2d_fwr_run(tmp_path: Path, n_electrodes=10, n_lines=3):
    opts = SyntheticsComponentsOptions(
        method="direct current 2d",
        survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
        mesh=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=50.0,
            expansion_factor=1.1,
            vertical_padding=100.0,
        ),
        model=ModelOptions(
            background=0.01,
            anomaly=10.0,
            plate=PlateModel(
                strike_length=1000.0,
                dip_length=150.0,
                width=20.0,
                origin=(0.0, 0.0, -50),
                direction=90,
                dip=45,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = DC2DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver = DC2DForwardDriver(params)
    fwr_driver.run()


def test_dc_rotated_gradient_2d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_dc_rotated_2d_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)

        fwr_group = geoh5.get_entity("Direct Current 2D Forward")[0]
        survey = fwr_group.get_entity("survey")[0]
        potential = survey.get_data("Iteration_0_potential")[0]
        # Create property group with orientation
        dip = np.ones(components.mesh.n_cells) * 45
        azimuth = np.ones(components.mesh.n_cells) * 90

        data_list = components.mesh.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            components.mesh,
            properties=data_list,
            property_group_type="Dip direction & dip",
        )

        # Run the inverse
        params = DC2DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=100.0,
                expansion_factor=1.1,
                horizontal_padding=1000.0,
                vertical_padding=1000.0,
            ),
            topography_object=components.topography,
            data_object=potential.parent,
            gradient_rotation=pg,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            cooling_rate=1,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    DC2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    basepath = workpath.parent
    with open(basepath / "lookup.json", encoding="utf8") as f:
        lookup = json.load(f)
        middle_line_id = next(k for k, v in lookup.items() if v["line_id"] == 101)

    with Workspace(basepath / f"{middle_line_id}.ui.geoh5", mode="r") as workspace:
        middle_inversion_group = next(
            k for k in workspace.groups if isinstance(k, SimPEGGroup)
        )

    output = get_inversion_output(
        basepath / f"{middle_line_id}.ui.geoh5", middle_inversion_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_dc_rotated_2d_fwr_run(Path("./"), n_electrodes=20, n_lines=3)
    test_dc_rotated_gradient_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
