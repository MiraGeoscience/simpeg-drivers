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

from simpeg_drivers.natural_sources.apparent_conductivity import (
    AppConForwardDriver,
    AppConForwardOptions,
    AppConInversionDriver,
    AppConInversionOptions,
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

target_run = {"data_norm": 0.018661818427023937, "phi_d": 502, "phi_m": 10900}


def test_app_con_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="apparent conductivity",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points,
            n_lines=n_grid_points,
            drape=15.0,
            topography=lambda x, y: np.zeros(x.shape),
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
            padding_distance=2000,
        ),
        model=ModelOptions(
            background=100.0,
            anomaly=1.0,
            plate=PlateModel(
                strike_length=60.0,
                dip_length=60.0,
                width=60.0,
                dip=90,
                easting=0.0,
                northing=0.0,
                elevation=-90.0,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        params = AppConForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            model_type="Resistivity (Ohm-m)",
            background_conductivity=1e2,
        )

    fwr_driver = AppConForwardDriver(params)

    # Should always be returning conductivity for simpeg simulations
    assert not np.any(np.exp(fwr_driver.models.starting_model) > 1.01)
    fwr_driver.run()


def test_app_con_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_app_con_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5=geoh5)
        survey = components.survey
        mesh = components.mesh
        topography = components.topography

        data = []
        uncertainties = []
        for ind in range(len(survey.channels)):
            data_entity = geoh5.get_entity(f"Iteration_0_app_con_[{ind}]")[0].copy(
                parent=survey
            )
            data.append(data_entity)

            # Assign uncertainties based on deviation from apparent conductivity of 0.01 S/m
            uncert = survey.add_data(
                {
                    f"uncertainty_[{ind}]": {
                        "values": np.full(
                            data_entity.values.shape[0],
                            (data_entity.values.max() - data_entity.values.min()) / 4,
                        )
                    }
                }
            )
            uncertainties.append(uncert)

        data_groups = survey.add_components_data({"Observed": data})[0]
        uncert_groups = survey.add_components_data({"Uncertainties": uncertainties})[0]

        orig_tyz_real_1 = geoh5.get_entity("Iteration_0_app_con_[0]")[0].values

        # Run the inverse
        params = AppConInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=topography,
            data_object=survey,
            starting_model=1e2,
            reference_model=None,
            background_conductivity=1e2,
            alpha_s=1.0,
            model_type="Resistivity (Ohm-m)",
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            cooling_rate=1,
            percentile=100,
            chi_factor=0.1,
            starting_chi_factor=0.1,
            max_line_search_iterations=5,
            app_con_channel=data_groups,
            app_con_uncertainty=uncert_groups,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        driver = AppConInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_tyz_real_1
        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_app_con_fwr_run(
        Path("./"), n_grid_points=8, cell_size=(10.0, 10.0, 10.0), refinement=(4, 4)
    )
    test_app_con_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
