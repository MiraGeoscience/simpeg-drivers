# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=too-many-locals

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup

from simpeg_drivers.electromagnetics.frequency_domain.driver import (
    FDEMForwardDriver,
    FDEMInversionDriver,
)
from simpeg_drivers.electromagnetics.frequency_domain.options import (
    FDEMForwardOptions,
    FDEMInversionOptions,
)
from simpeg_drivers.utils.testing_utils.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticDataInversionOptions,
)
from simpeg_drivers.utils.testing_utils.runtests import (
    setup_inversion_workspace,
)
from tests.utils.targets import (
    check_target,
    get_inversion_output,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 81.8361, "phi_d": 2160, "phi_m": 4010}


def test_fem_name_change(tmp_path, caplog):
    # Run the forward
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(n_stations=2, n_lines=2, drape=15.0),
        mesh=MeshOptions(refinement=(2,), padding_distance=400.0),
        model=ModelOptions(background=1e-3),
    )
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="fdem", options=opts
    )
    with caplog.at_level(logging.WARNING):
        FDEMForwardOptions.build(
            geoh5=geoh5,
            mesh=model.parent,
            topography_object=topography,
            data_object=survey,
            starting_model=model,
            z_real_channel_bool=True,
            z_imag_channel_bool=True,
            inversion_type="fem",
        )
    assert "fdem" in caplog.text


def test_fem_fwr_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points,
            n_lines=n_grid_points,
            drape=15.0,
            terrain=lambda x, y: np.zeros(x.shape),
        ),
        mesh=MeshOptions(
            cell_size=cell_size, refinement=refinement, padding_distance=400.0
        ),
        model=ModelOptions(
            background=1e-3,
            plate=PlateModel(
                strike_length=40.0,
                dip_length=40.0,
                width=40.0,
                origin=(0.0, 0.0, -50.0),
            ),
        ),
    )
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        method="fdem",
        options=opts,
    )
    params = FDEMForwardOptions.build(
        geoh5=geoh5,
        mesh=model.parent,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
        z_real_channel_bool=True,
        z_imag_channel_bool=True,
    )

    fwr_driver = FDEMForwardDriver(params)
    fwr_driver.run()


def test_fem_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_fem_fwr_run0" / "inversion_test.ui.geoh5"

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
            "z_real": "z_real",
            "z_imag": "z_imag",
        }

        for comp, cname in components.items():
            data[cname] = []
            uncertainties[f"{cname} uncertainties"] = []
            for ind, freq in enumerate(survey.channels):
                data_entity = geoh5.get_entity(f"Iteration_0_{comp}_[{ind}]")[0].copy(
                    parent=survey
                )
                data[cname].append(data_entity)
                abs_val = np.abs(data_entity.values)
                uncert = survey.add_data(
                    {
                        f"uncertainty_{comp}_[{ind}]": {
                            "values": np.ones_like(abs_val)
                            * freq
                            / 200.0  # * 2**(np.abs(ind-1))
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(
                    uncert.copy(parent=survey)
                )

        data_groups = survey.add_components_data(data)
        uncert_groups = survey.add_components_data(uncertainties)

        data_kwargs = {}
        for comp, data_group, uncert_group in zip(
            components, data_groups, uncert_groups, strict=True
        ):
            data_kwargs[f"{comp}_channel"] = data_group
            data_kwargs[f"{comp}_uncertainty"] = uncert_group

        orig_z_real_1 = geoh5.get_entity("Iteration_0_z_real_[0]")[0].values

        # Run the inverse
        params = FDEMInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=topography,
            data_object=survey,
            starting_model=1e-3,
            reference_model=1e-3,
            alpha_s=0.0,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            upper_bound=0.75,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e1,
            percentile=100,
            cooling_rate=3,
            chi_factor=0.25,
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        driver = FDEMInversionDriver(params)
        driver.run()

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_z_real_1

        assert (
            run_ws.get_entity("Iteration_1_z_imag_[1]")[0].entity_type.uid
            == run_ws.get_entity("Observed_z_imag_[1]")[0].entity_type.uid
        )

        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_fem_fwr_run(
        Path("./"),
        n_grid_points=5,
        cell_size=(5.0, 5.0, 5.0),
        refinement=(4, 4, 4),
    )
    test_fem_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
