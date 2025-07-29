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
from pytest import raises

from simpeg_drivers.electromagnetics.time_domain_1d.driver import (
    TDEM1DForwardDriver,
    TDEM1DInversionDriver,
)
from simpeg_drivers.electromagnetics.time_domain_1d.options import (
    TDEM1DForwardOptions,
    TDEM1DInversionOptions,
)
from simpeg_drivers.options import ActiveCellsOptions
from tests.testing_utils import (
    check_target,
    get_inversion_output,
    setup_inversion_workspace,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.
target_run = {"data_norm": 6.15712e-10, "phi_d": 109, "phi_m": 102000}


def test_airborne_tem_1d_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.1,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        cell_size=cell_size,
        refinement=refinement,
        inversion_type="airborne tdem 1d",
        drape_height=10.0,
        padding_distance=400.0,
        flatten=False,
    )
    params = TDEM1DForwardOptions.build(
        geoh5=geoh5,
        mesh=model.parent,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
        z_channel_bool=True,
        solver_type="Mumps",
    )

    fwr_driver = TDEM1DForwardDriver(params)

    fwr_driver.run()


def test_airborne_tem_1d_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_airborne_tem_1d_fwr_run0"
            / "inversion_test.ui.geoh5"
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
                            * (np.percentile(np.abs(data_entity.values), 10) / 2.0)
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(uncert)

        survey.add_components_data(data)
        survey.add_components_data(uncertainties)

        data_kwargs = {}
        for comp in components:
            data_kwargs[f"{comp}_channel"] = survey.fetch_property_group(
                name=f"dB{comp}dt"
            )
            data_kwargs[f"{comp}_uncertainty"] = survey.fetch_property_group(
                name=f"dB{comp}dt uncertainties"
            )

        orig_dBzdt = geoh5.get_entity("Iteration_0_z_[0]")[0].values

        # Run the inverse
        params = TDEM1DInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=topography,
            data_object=survey,
            starting_model=5e-1,
            reference_model=1e-1,
            s_norm=0.0,
            x_norm=2.0,
            z_norm=0.0,
            length_scale_x=1e-4,
            lower_bound=1e-4,
            upper_bound=1e2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-2,
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = TDEM1DInversionDriver(params)
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
    test_airborne_tem_1d_fwr_run(
        Path("./"), n_grid_points=5, cell_size=(5.0, 5.0, 5.0), refinement=(0, 0, 4)
    )
    test_airborne_tem_1d_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
