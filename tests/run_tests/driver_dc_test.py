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
    DC3DForwardDriver,
    DC3DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.three_dimensions.options import (
    DC3DForwardOptions,
    DC3DInversionOptions,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
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

target_run = {"data_norm": 0.1503264550032795, "phi_d": 43.9, "phi_m": 935}


def test_dc_3d_fwr_run(
    tmp_path: Path,
    n_electrodes=4,
    n_lines=3,
    refinement=(4, 6),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="direct current 3d",
        survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(background=0.01, anomaly=10.0),
    )
    with Workspace.create(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        # Randomly flip order of receivers
        old = np.random.randint(0, components.survey.cells.shape[0], n_electrodes)
        indices = np.ones(components.survey.cells.shape[0], dtype=bool)
        indices[old] = False

        tx_id = np.r_[
            components.survey.ab_cell_id.values[indices],
            components.survey.ab_cell_id.values[~indices],
        ]
        cells = np.vstack(
            [components.survey.cells[indices, :], components.survey.cells[~indices, :]]
        )

        components.survey.ab_cell_id = tx_id
        components.survey.cells = cells

        params = DC3DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver = DC3DForwardDriver(params)
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
        components = SyntheticsComponents(geoh5)
        potential = geoh5.get_entity("Iteration_0_potential")[0]

        # Run the inverse
        params = DC3DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=potential.parent,
            starting_model=1e-2,
            reference_model=1e-2,
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            potential_channel=potential,
            potential_uncertainty=1e-3,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            tile_spatial=n_lines,
            auto_scale_misfits=False,
            save_sensitivities=True,
            cooling_rate=1,
            chi_factor=0.5,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC3DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))
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
    opts = SyntheticsComponentsOptions(
        method="direct current 3d",
        survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(background=0.01, anomaly=10.0),
    )
    with Workspace.create(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = DC3DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )

    fwr_driver = DC3DForwardDriver(params)
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
