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

from pathlib import Path

import numpy as np
from geoh5py.groups import SimPEGGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.natural_sources.magnetotellurics.driver import (
    MTForwardDriver,
    MTInversionDriver,
)
from simpeg_drivers.natural_sources.magnetotellurics.params import (
    MTForwardOptions,
    MTInversionOptions,
)
from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.032649770, "phi_d": 6.676, "phi_m": 212.3}


def test_magnetotellurics_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.01,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        cell_size=cell_size,
        drape_height=0.0,
        inversion_type="magnetotellurics",
        flatten=False,
    )
    params = MTForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=ActiveCellsOptions(topography_object=topography),
        data_object=survey,
        starting_model=model,
        background_conductivity=1e-2,
        zxx_real_channel_bool=True,
        zxx_imag_channel_bool=True,
        zxy_real_channel_bool=True,
        zxy_imag_channel_bool=True,
        zyx_real_channel_bool=True,
        zyx_imag_channel_bool=True,
        zyy_real_channel_bool=True,
        zyy_imag_channel_bool=True,
    )

    fwr_driver = MTForwardDriver(params)
    fwr_driver.run()


def test_magnetotellurics_run(tmp_path: Path, max_iterations=1, pytest=True):
    # pass
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_magnetotellurics_fwr_run0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        survey = next(
            child
            for child in geoh5.get_entity("survey")
            if not isinstance(child.parent, SimPEGGroup)
        )
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        data = {}
        uncertainties = {}
        components = {
            "zxx_real": "Zxx (real)",
            "zxx_imag": "Zxx (imag)",
            "zxy_real": "Zxy (real)",
            "zxy_imag": "Zxy (imag)",
            "zyx_real": "Zyx (real)",
            "zyx_imag": "Zyx (imag)",
            "zyy_real": "Zyy (real)",
            "zyy_imag": "Zyy (imag)",
        }

        for comp, cname in components.items():
            data[cname] = []
            # uncertainties[f"{cname} uncertainties"] = {}
            uncertainties[f"{cname} uncertainties"] = []
            for ind in range(len(survey.channels)):
                data_entity = geoh5.get_entity(f"Iteration_0_{comp}_[{ind}]")[0].copy(
                    parent=survey
                )
                data[cname].append(data_entity)

                uncert = survey.add_data(
                    {
                        f"uncertainty_{comp}_[{ind}]": {
                            "values": np.ones_like(data_entity.values)
                            * np.percentile(np.abs(data_entity.values), 5)
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

        orig_zyy_real_1 = geoh5.get_entity("Iteration_0_zyy_real_[0]")[0].values

        # Run the inverse
        params = MTInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=ActiveCellsOptions(topography_object=topography),
            data_object=survey,
            starting_model=100.0,
            reference_model=100.0,
            alpha_s=1.0,
            s_norm=1.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            cooling_rate=1,
            lower_bound=0.75,
            model_type="Resistivity (Ohm-m)",
            background_conductivity=100.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e3,
            sens_wts_threshold=1.0,
            percentile=100,
            store_sensitivities="ram",
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        driver = MTInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    with geoh5.open() as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )
        output["data"] = orig_zyy_real_1
        if pytest:
            check_target(output, target_run, tolerance=0.5)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)

    # test that one channel works
    data_kwargs = {k: v for k, v in data_kwargs.items() if "zxx_real" in k}
    geoh5.open()
    params = MTInversionOptions(
        geoh5=geoh5,
        mesh=geoh5.get_entity("mesh")[0],
        active_cells=ActiveCellsOptions(topography_object=topography),
        data_object=survey,
        starting_model=0.01,
        background_conductivity=1e-2,
        max_global_iterations=0,
        **data_kwargs,
    )
    params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
    MTInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))


if __name__ == "__main__":
    # Full run
    test_magnetotellurics_fwr_run(
        Path("./"), n_grid_points=8, cell_size=(5.0, 5.0, 5.0), refinement=(4, 8)
    )
    test_magnetotellurics_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
