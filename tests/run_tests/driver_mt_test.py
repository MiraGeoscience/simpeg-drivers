# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=too-many-locals

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoh5py.workspace import Workspace

from simpeg_drivers.natural_sources.magnetotellurics.driver import (
    MagnetotelluricsDriver,
)
from simpeg_drivers.natural_sources.magnetotellurics.params import (
    MagnetotelluricsParams,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output

# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.003936, "phi_d": 1.824, "phi_m": 2.551}


def test_magnetotellurics_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.01,
        anomaly=1.0,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        drape_height=0.0,
        inversion_type="magnetotellurics",
        flatten=False,
    )
    params = MagnetotelluricsParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        resolution=0.0,
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
        conductivity_model=1e-2,
        zxx_real_channel_bool=True,
        zxx_imag_channel_bool=True,
        zxy_real_channel_bool=True,
        zxy_imag_channel_bool=True,
        zyx_real_channel_bool=True,
        zyx_imag_channel_bool=True,
        zyy_real_channel_bool=True,
        zyy_imag_channel_bool=True,
    )
    params.workpath = tmp_path
    fwr_driver = MagnetotelluricsDriver(params)
    fwr_driver.run()


def test_magnetotellurics_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent
            / "test_magnetotellurics_fwr_run0"
            / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        survey = geoh5.get_entity("survey")[0].copy(copy_children=False)
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
                            * np.percentile(np.abs(data_entity.values), 10)
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
            components, data_groups, uncert_groups
        ):
            data_kwargs[f"{comp}_channel"] = data_group.uid
            data_kwargs[f"{comp}_uncertainty"] = uncert_group.uid

        orig_zyy_real_1 = geoh5.get_entity("Iteration_0_zyy_real_[0]")[0].values

        # Run the inverse
        params = MagnetotelluricsParams(
            geoh5=geoh5,
            mesh=mesh.uid,
            topography_object=topography.uid,
            resolution=0.0,
            data_object=survey.uid,
            starting_model=0.01,
            reference_model=0.01,
            alpha_s=1.0,
            s_norm=1.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            z_from_topo=False,
            upper_bound=0.75,
            conductivity_model=1e-2,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e2,
            prctile=100,
            store_sensitivities="ram",
            **data_kwargs,
        )
        params.write_input_file(path=tmp_path, name="Inv_run")
        driver = MagnetotelluricsDriver.start(str(tmp_path / "Inv_run.ui.json"))

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
    params = MagnetotelluricsParams(
        geoh5=geoh5,
        mesh=geoh5.get_entity("mesh")[0].uid,
        topography_object=topography.uid,
        data_object=survey.uid,
        starting_model=0.01,
        conductivity_model=1e-2,
        max_global_iterations=0,
        # store_sensitivities="ram",
        **data_kwargs,
    )
    params.write_input_file(path=tmp_path, name="Inv_run")
    MagnetotelluricsDriver.start(str(tmp_path / "Inv_run.ui.json"))


if __name__ == "__main__":
    # Full run
    test_magnetotellurics_fwr_run(Path("./"), n_grid_points=8, refinement=(4, 8))
    test_magnetotellurics_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
