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

from logging import getLogger
from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.workspace import Workspace
from pymatsolver.direct import Mumps

from simpeg_drivers.electromagnetics.borehole_time_domain.forward import (
    BoreholeTDEMForwardDriver,
    BoreholeTDEMForwardOptions,
)
from simpeg_drivers.electromagnetics.borehole_time_domain.inversion import (
    BoreholeTDEMInversionDriver,
    BoreholeTDEMInversionOptions,
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


logger = getLogger(__name__)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 6.3414e-11, "phi_d": 1.1820e04, "phi_m": 9.7920e02}


def test_borehole_tem_fwr_run(
    tmp_path: Path,
    n_grid_points=4,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="borehole tdem",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=n_grid_points * 2,
            n_lines=n_grid_points,
            drape=5.0,
            topography=lambda x, y: np.zeros(x.shape),
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
            padding_distance=1000.0,
        ),
        model=ModelOptions(
            background=0.001,
            plate=PlateModel(
                strike_length=40.0,
                dip_length=40.0,
                width=40.0,
                easting=-40.0,
                northing=0.0,
                elevation=-75.0,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = BoreholeTDEMForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            a_channel_bool=True,
            u_channel_bool=True,
            v_channel_bool=True,
            solver_type="Mumps",
            data_units="Ground B (T/A)",
        )

    fwr_driver = BoreholeTDEMForwardDriver(params)
    fwr_driver.run()


def test_borehole_tem_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_borehole_tem_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)
        data = {}
        uncertainties = {}
        channels = {
            "a": "a",
            "u": "u",
            "v": "v",
        }

        for chan in channels:
            data[chan] = []
            uncertainties[f"{chan} uncertainties"] = []
            for ii, _ in enumerate(components.survey.channels):
                data_entity = geoh5.get_entity(f"Iteration_0_{chan}_[{ii}]")[0].copy(
                    parent=components.survey
                )
                data[chan].append(data_entity)

                uncert = components.survey.add_data(
                    {
                        f"uncertainty_{chan}_[{ii}]": {
                            "values": np.abs(data_entity.values) * 0.05 + 3e-13
                        }
                    }
                )
                uncertainties[f"{chan} uncertainties"].append(uncert)

        components.survey.add_components_data(data)
        components.survey.add_components_data(uncertainties)

        data_kwargs = {}
        for chan in channels:
            data_kwargs[f"{chan}_channel"] = components.survey.fetch_property_group(
                name=f"{chan}"
            )
            data_kwargs[f"{chan}_uncertainty"] = components.survey.fetch_property_group(
                name=f"{chan} uncertainties"
            )

        orig_dBzdt = geoh5.get_entity("Iteration_0_a_[0]")[0].values

        # Run the inverse
        params = BoreholeTDEMInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=3e-3,
            reference_model=1e-3,
            chi_factor=0.1,
            s_norm=0.0,
            x_norm=2.0,
            y_norm=2.0,
            z_norm=2.0,
            alpha_s=0e-0,
            lower_bound=2e-6,
            upper_bound=1e2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            starting_chi_factor=1000,
            cooling_rate=1,
            max_cg_iterations=200,
            percentile=5,
            sens_wts_threshold=1.0,
            solver_type="Mumps",
            data_units="Ground B (T/A)",
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = BoreholeTDEMInversionDriver(params)
    driver.run()

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        assert driver.inversion_data.entity.tx_id_property.name == "Transmitter ID"
        output["data"] = orig_dBzdt
        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_borehole_tem_fwr_run(
        Path("./"),
        n_grid_points=5,
        refinement=(2, 2, 2),
        cell_size=(5.0, 5.0, 5.0),
    )
    test_borehole_tem_run(
        Path("./"),
        max_iterations=10,
        pytest=False,
    )
