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
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.two_dimensions import (
    DC2DForwardDriver,
    DC2DForwardOptions,
    DC2DInversionDriver,
    DC2DInversionOptions,
)
from simpeg_drivers.options import (
    DrapeModelOptions,
    LineSelectionOptions,
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

target_run = {"data_norm": 11.14351536256954, "phi_d": 6360, "phi_m": 245}


def test_dc_2d_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="direct current 2d",
        survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
        mesh=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=50.0,
            expansion_factor=1.1,
            vertical_padding=200.0,
            horizontal_padding=200.0,
        ),
        model=ModelOptions(
            background=0.001,
            anomaly=1.0,
            plate=PlateModel(
                strike_length=1000.0,
                dip_length=20.0,
                width=20.0,
                easting=0.0,
                northing=0.0,
                elevation=0.0,
                direction=90,
                dip=90,
            ),
        ),
    )

    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5=geoh5, options=opts)
        line_ids = components.survey.get_data("line_ids")[0]
        params = DC2DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            line_selection=LineSelectionOptions(property=line_ids, value=[1, 101, 201]),
        )
    fwr_driver = DC2DForwardDriver(params)
    fwr_driver.run()


def test_dc_2d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_dc_2d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)
        fwr_group = geoh5.get_entity("Direct Current 2D Forward")[0]
        survey = fwr_group.get_entity("survey")[0]
        potential = survey.get_data("Iteration_0_potential")[0]
        uncertainties = survey.add_data(
            {
                "Uncertainties": {
                    "values": np.abs(potential.values) * 0.05 + 1e-4,
                }
            }
        )
        # Run the inverse
        params = DC2DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=potential.parent,
            potential_channel=potential,
            potential_uncertainty=uncertainties,
            starting_model=1e-3,
            reference_model=1e-3,
            s_norm=0.0,
            x_norm=1.0,
            z_norm=1.0,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            cooling_rate=1,
        )
        # TODO Fix the write for MultiSelect of Reference data
        # params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC2DInversionDriver(params)
    driver.run()
    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


def test_dc_single_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_dc_2d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)
        fwr_group = geoh5.get_entity("Direct Current 2D Forward")[0]
        survey = fwr_group.get_entity("survey")[0]
        potential = survey.get_data("Iteration_0_potential")[0]
        uncertainties = survey.add_data(
            {
                "Uncertainties": {
                    "values": np.abs(potential.values) * 0.05 + 1e-4,
                }
            }
        )

        line_ids = survey.get_data("line_ids")[0]

        # Run the inverse
        params = DC2DInversionOptions.build(
            geoh5=geoh5,
            title="Direct Current Single 2D Inversion",
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=potential.parent,
            potential_channel=potential,
            potential_uncertainty=uncertainties,
            line_selection=LineSelectionOptions(property=line_ids, value=[101]),
            starting_model=1e-3,
            reference_model=1e-3,
            s_norm=0.0,
            x_norm=1.0,
            z_norm=1.0,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            cooling_rate=1,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC2DInversionDriver(params)
    driver.run()

    with Workspace(workpath) as geoh5:
        inv_group = geoh5.get_entity("Direct Current Single 2D Inversion")[0]
        mesh = inv_group.get_entity("mesh")[0]
        model = mesh.get_entity("Iteration_1_model")[0]

        # Check that model values for lines 1 and 3 are close to the starting model (1e-3) and that line 2 has been updated.
        np.testing.assert_almost_equal(np.nanmax(model.values[:2369]), 1e-3, decimal=3)
        np.testing.assert_almost_equal(np.nanmax(model.values[-2368:]), 1e-3, decimal=3)
        assert np.nanmax(model.values[2368:-2368]) > 1e-3


if __name__ == "__main__":
    # Full run
    test_dc_2d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=3,
    )
    test_dc_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
