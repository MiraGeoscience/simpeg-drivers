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

import shutil
from io import BytesIO
from pathlib import Path

import numpy as np
from geoh5py.ui_json import UIJson
from geoh5py.workspace import Workspace
from pandas import read_csv

from simpeg_drivers.electromagnetics.time_domain_1d.forward import (
    TDEM1DForwardDriver,
    TDEM1DForwardOptions,
)
from simpeg_drivers.electromagnetics.time_domain_1d.inversion import (
    TDEM1DInversionDriver,
    TDEM1DInversionOptions,
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
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.
target_run = {"data_norm": 4.1821e-10, "phi_d": 5.7170e01, "phi_m": 1.2470e04}


def test_airborne_tem_1d_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
    cell_size=(10.0, 10.0, 10.0),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="airborne tdem 1d",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=10.0
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
            padding_distance=400.0,
        ),
        model=ModelOptions(background=0.1),
    )
    with get_workspace(tmp_path / "inversion_test.geoh5") as geoh5:
        components = SyntheticsComponents(
            geoh5,
            options=opts,
        )
        params = TDEM1DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            z_channel_bool=True,
            solver_type="Mumps",
        )

    fwr_driver = TDEM1DForwardDriver(params)

    fwr_driver.run()


def test_airborne_tem_1d_run(tmp_path: Path, max_iterations=3, pytest=True):
    workpath = tmp_path / "inversion_test.geoh5"

    if pytest:
        shutil.copy(
            tmp_path.parent / "test_airborne_tem_1d_fwr_run0" / "inversion_test.geoh5",
            tmp_path,
        )

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5=geoh5)
        data = {}
        uncertainties = {}
        channels = {
            "vertical": "vertical",
        }
        mesh = geoh5.get_entity("Draped Model")[0]
        for chan, cname in channels.items():
            data[cname] = []
            uncertainties[f"{cname} uncertainties"] = []
            for ii, _ in enumerate(components.survey.channels):
                data_entity = geoh5.get_entity(f"Iteration_0_{chan}_[{ii}]")[0].copy(
                    parent=components.survey
                )
                data[cname].append(data_entity)

                uncert = components.survey.add_data(
                    {
                        f"uncertainty_{chan}_[{ii}]": {
                            "values": np.ones_like(data_entity.values)
                            * (np.percentile(np.abs(data_entity.values), 10) / 2.0)
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(uncert)

        components.survey.add_components_data(data)
        components.survey.add_components_data(uncertainties)

        data_kwargs = {}
        for chan in channels:
            data_kwargs[f"{chan}_channel"] = components.survey.fetch_property_group(
                name="vertical"
            )
            data_kwargs[f"{chan}_uncertainty"] = components.survey.fetch_property_group(
                name="vertical uncertainties"
            )

        orig_dBzdt = geoh5.get_entity("Iteration_0_vertical_[0]")[0].values

        # Run the inverse
        params = TDEM1DInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=5e-1,
            reference_model=1e-1,
            s_norm=0.0,
            x_norm=2.0,
            z_norm=0.0,
            length_scale_x=1e-4,
            lower_bound=1e-4,
            upper_bound=1e2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-0,
            cooling_rate=1,
            **data_kwargs,
        )
        params.out_group = params.ui_json.to_ui_json_group(workspace=geoh5)
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

        driver = TDEM1DInversionDriver(params)

        if pytest:
            # Mock workers and check if the list shrinks to number of stations
            driver._workers = [None] * 100  # pylint: disable=protected-access

            driver.get_tiles()  # Trigger reset
            assert len(driver.workers) == 9

            # Mock with fewer workers
            driver._workers = [None] * 4  # pylint: disable=protected-access
            driver.get_tiles()  # Trigger reset
            assert len(driver.workers) == 4

            # Mock with small chunks
            driver.params.compute.max_chunk_size = 1
            driver.get_tiles()  # Trigger reset
            assert len(driver.workers) == 4

            # Reset and run
            driver._workers = []  # pylint: disable=protected-access

    driver.run()

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_dBzdt
        if pytest:
            check_target(output, target_run, tolerance=0.1)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


def test_restart_run(tmp_path):
    shutil.copy(
        tmp_path.parent / "test_airborne_tem_1d_run0" / "Inv_run.ui.json", tmp_path
    )
    shutil.copy(
        tmp_path.parent / "test_airborne_tem_1d_run0" / "inversion_test.geoh5", tmp_path
    )
    json_file = tmp_path / "Inv_run.ui.json"

    # Remember the last iteration
    out_array = read_csv(
        tmp_path.parent / "test_airborne_tem_1d_run0/inversion_test.out", sep=" "
    )

    last_beta = out_array["beta"].iloc[-1]
    last_phi_d = out_array["phi_d"].iloc[-1]
    last_phi_m = out_array["phi_m"].iloc[-1]

    uijson = UIJson.read(json_file)
    uijson.geoh5 = tmp_path / "inversion_test.geoh5"
    uijson.set_values(max_global_iterations=5)
    uijson.write(json_file)
    TDEM1DInversionDriver.start_dask_run(
        json_file, start_iteration=-2, n_workers=1, n_threads=1
    )

    # Read the out file again and check against the previous full run
    with Workspace(tmp_path / "inversion_test.geoh5") as ws:
        out_file = ws.get_entity("inversion_test.out")[0]
        out_array = read_csv(BytesIO(out_file.file_bytes), sep=" ")
        np.testing.assert_almost_equal(out_array["beta"].iloc[5], last_beta, decimal=1)
        np.testing.assert_almost_equal(
            out_array["phi_d"].iloc[5], last_phi_d, decimal=1
        )
        np.testing.assert_almost_equal(
            out_array["phi_m"].iloc[5], last_phi_m, decimal=1
        )


if __name__ == "__main__":
    # Full run
    test_airborne_tem_1d_fwr_run(
        Path("./"), n_grid_points=5, cell_size=(5.0, 5.0, 5.0), refinement=(0, 0, 4)
    )
    test_airborne_tem_1d_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
