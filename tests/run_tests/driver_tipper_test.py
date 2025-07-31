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

from simpeg_drivers.natural_sources.tipper import (
    TipperForwardOptions,
    TipperInversionOptions,
)
from simpeg_drivers.natural_sources.tipper.driver import (
    TipperForwardDriver,
    TipperInversionDriver,
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
from simpeg_drivers.utils.testing_utils.targets import (
    check_target,
    get_inversion_output,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.006549595419474837, "phi_d": 221, "phi_m": 270}


def test_tipper_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=15.0
        ),
        mesh=MeshOptions(cell_size=cell_size, refinement=refinement),
        model=ModelOptions(background=100.0),
    )
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="tipper", options=opts
    )

    params = TipperForwardOptions.build(
        geoh5=geoh5,
        mesh=model.parent,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
        model_type="Resistivity (Ohm-m)",
        background_conductivity=1e2,
        txz_real_channel_bool=True,
        txz_imag_channel_bool=True,
        tyz_real_channel_bool=True,
        tyz_imag_channel_bool=True,
    )

    fwr_driver = TipperForwardDriver(params)

    # Should always be returning conductivity for simpeg simulations
    assert not np.any(np.exp(fwr_driver.models.starting_model) > 1.01)
    fwr_driver.run()


def test_tipper_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_tipper_fwr_run0" / "inversion_test.ui.geoh5"

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
            "txz_real": "Txz (real)",
            "txz_imag": "Txz (imag)",
            "tyz_real": "Tyz (real)",
            "tyz_imag": "Tyz (imag)",
        }

        for comp, cname in components.items():
            data[cname] = []
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
                            * np.percentile(np.abs(data_entity.values), 1)
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(uncert)

        data_groups = survey.add_components_data(data)
        uncert_groups = survey.add_components_data(uncertainties)

        data_kwargs = {}
        for comp, data_group, uncert_group in zip(
            components, data_groups, uncert_groups, strict=True
        ):
            data_kwargs[f"{comp}_channel"] = data_group
            data_kwargs[f"{comp}_uncertainty"] = uncert_group

        orig_tyz_real_1 = geoh5.get_entity("Iteration_0_tyz_real_[0]")[0].values

        # Run the inverse
        params = TipperInversionOptions.build(
            geoh5=geoh5,
            mesh=mesh,
            topography_object=topography,
            data_object=survey,
            starting_model=1e2,
            reference_model=1e2,
            background_conductivity=1e2,
            s_norm=1.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            alpha_s=1.0,
            model_type="Resistivity (Ohm-m)",
            lower_bound=0.75,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e3,
            starting_chi_factor=1.0,
            cooling_rate=1,
            percentile=100,
            chi_factor=1.0,
            max_line_search_iterations=5,
            **data_kwargs,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")
        driver = TipperInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

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
    test_tipper_fwr_run(
        Path("./"), n_grid_points=8, cell_size=(5.0, 5.0, 5.0), refinement=(4, 4)
    )
    test_tipper_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
