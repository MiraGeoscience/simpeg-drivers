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
from geoh5py.groups import SimPEGGroup
from geoh5py.workspace import Workspace
from pymatsolver.direct import Mumps
from pytest import raises

from simpeg_drivers.electromagnetics.time_domain import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)
from simpeg_drivers.electromagnetics.time_domain.driver import (
    TDEMForwardDriver,
    TDEMInversionDriver,
)
from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 7.05481e-08, "phi_d": 198200000, "phi_m": 7806}


def test_bad_waveform(tmp_path: Path):
    n_grid_points = 3
    refinement = (2,)
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.001,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        inversion_type="airborne_tem",
        drape_height=10.0,
        padding_distance=400.0,
        flatten=False,
    )
    params = TDEMForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=ActiveCellsOptions(topography_object=topography),
        data_object=survey,
        starting_model=model,
        x_channel_bool=True,
        y_channel_bool=True,
        z_channel_bool=True,
    )

    fwr_driver = TDEMForwardDriver(params)

    survey.channels[-1] = 1000.0

    with raises(ValueError, match="The latest time"):
        _ = fwr_driver.inversion_data.survey


def test_airborne_tem_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.001,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        cell_size=cell_size,
        refinement=refinement,
        inversion_type="airborne_tem",
        drape_height=10.0,
        padding_distance=400.0,
        flatten=False,
    )
    params = TDEMForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=ActiveCellsOptions(topography_object=topography),
        data_object=survey,
        starting_model=model,
        x_channel_bool=True,
        y_channel_bool=True,
        z_channel_bool=True,
    )

    fwr_driver = TDEMForwardDriver(params)

    fwr_driver.data_misfit.objfcts[0].simulation.solver = Mumps
    fwr_driver.run()


def test_airborne_tem_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_airborne_tem_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        survey = next(
            child
            for child in geoh5.get_entity("Airborne_rx")
            if not isinstance(child.parent, SimPEGGroup)
        )
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        data = {}
        uncertainties = {}
        components = {
            "z": "dBzdt",
        }

        for comp, cname in components.items():
            data[cname] = []
            uncertainties[f"{cname} uncertainties"] = []
            for ii, _ in enumerate(survey.channels):
                data_entity = geoh5.get_entity(f"Iteration_0_{comp}_[{ii}]")[0].copy(
                    parent=survey
                )
                data[cname].append(data_entity)

                uncert = survey.add_data(
                    {
                        f"uncertainty_{comp}_[{ii}]": {
                            "values": np.ones_like(data_entity.values)
                            * (np.median(np.abs(data_entity.values)))
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(uncert)

        survey.add_components_data(data)
        survey.add_components_data(uncertainties)

        data_kwargs = {}
        for comp in components:
            data_kwargs[f"{comp}_channel"] = survey.find_or_create_property_group(
                name=f"dB{comp}dt"
            )
            data_kwargs[f"{comp}_uncertainty"] = survey.find_or_create_property_group(
                name=f"dB{comp}dt uncertainties"
            )

        orig_dBzdt = geoh5.get_entity("Iteration_0_z_[0]")[0].values

        # Run the inverse
        params = TDEMInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=ActiveCellsOptions(topography_object=topography),
            data_object=survey,
            starting_model=1e-3,
            reference_model=1e-3,
            chi_factor=1.0,
            s_norm=2.0,
            x_norm=2.0,
            y_norm=2.0,
            z_norm=2.0,
            alpha_s=1e-4,
            gradient_type="total",
            lower_bound=2e-6,
            upper_bound=1e2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e2,
            coolingRate=4,
            max_cg_iterations=200,
            prctile=5,
            sens_wts_threshold=1.0,
            store_sensitivities="ram",
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = TDEMInversionDriver(params)
    driver.data_misfit.objfcts[0].simulation.solver = Mumps
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


if __name__ == "__main__":
    # Full run
    test_airborne_tem_fwr_run(
        Path("./"), n_grid_points=5, cell_size=(5.0, 5.0, 5.0), refinement=(0, 0, 4)
    )
    test_airborne_tem_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
