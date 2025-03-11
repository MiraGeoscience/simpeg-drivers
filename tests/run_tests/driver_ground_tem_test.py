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

from logging import INFO, getLogger
from pathlib import Path

import numpy as np
from geoh5py.workspace import Workspace
from pymatsolver.direct import Mumps

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


logger = getLogger(__name__)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 8.806897e-07, "phi_d": 152.8, "phi_m": 12850}


def test_tiling_ground_tem(
    tmp_path: Path,
    *,
    n_grid_points=4,
    refinement=(2,),
    **_,
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.001,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        inversion_type="ground_tem",
        drape_height=5.0,
        padding_distance=1000.0,
        flatten=True,
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
        tile_spatial=4,
    )
    fwr_driver = TDEMForwardDriver(params)

    tiles = fwr_driver.get_tiles()

    assert len(tiles) == 4

    for tile in tiles:
        assert len(np.unique(survey.tx_id_property.values[tile])) == 1

    fwr_driver.run()


def test_ground_tem_fwr_run(
    tmp_path: Path,
    caplog,
    n_grid_points=4,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
    pytest=True,
):
    if pytest:
        caplog.set_level(INFO)
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.001,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        inversion_type="ground_tem",
        drape_height=5.0,
        cell_size=cell_size,
        padding_distance=1000.0,
        flatten=True,
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
        solver_type="Mumps",
    )

    fwr_driver = TDEMForwardDriver(params)

    with survey.workspace.open():
        survey.transmitters.remove_cells([15])
        survey.tx_id_property.name = "tx_id"
        assert fwr_driver.inversion_data.survey.source_list[0].n_segments == 16

    if pytest:
        assert len(caplog.records) == 2
        for record in caplog.records:
            assert record.levelname == "INFO"
            assert "counter-clockwise" in record.message

        assert "closed" in caplog.records[0].message

    assert fwr_driver.data_misfit.objfcts[0].simulation.simulations[0].solver == Mumps
    fwr_driver.run()


def test_ground_tem_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_ground_tem_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        simpeg_group = geoh5.get_entity("Time-domain EM (TEM) Forward")[0]
        survey = simpeg_group.get_entity("Ground TEM Rx")[0]
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
                            * np.median(np.abs(data_entity.values))
                            / 2.0
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(uncert)

        survey.add_components_data(data)
        survey.add_components_data(uncertainties)

        data_kwargs = {}
        for comp in components:
            data_kwargs[f"{comp}_channel"] = survey.fetch_property_group(
                name=f"Iteration_0_{comp}"
            )
            data_kwargs[f"{comp}_uncertainty"] = survey.fetch_property_group(
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
            chi_factor=0.1,
            s_norm=2.0,
            x_norm=2.0,
            y_norm=2.0,
            z_norm=2.0,
            alpha_s=0e-1,
            gradient_type="total",
            lower_bound=2e-6,
            upper_bound=1e2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            coolingRate=2,
            max_cg_iterations=200,
            prctile=100,
            sens_wts_threshold=1.0,
            store_sensitivities="ram",
            solver_type="Mumps",
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = TDEMInversionDriver(params)
    driver.run()

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        assert driver.inversion_data.entity.tx_id_property.name == "tx_id"
        output["data"] = orig_dBzdt
        if pytest:
            check_target(output, target_run, tolerance=0.1)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_ground_tem_fwr_run(
        Path("./"),
        None,
        n_grid_points=5,
        refinement=(2, 2, 2),
        cell_size=(5.0, 5.0, 5.0),
        pytest=False,
    )
    test_ground_tem_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
