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
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup

from simpeg_drivers.electromagnetics.frequency_domain_1d.driver import (
    FDEM1DForwardDriver,
    FDEM1DInversionDriver,
)
from simpeg_drivers.electromagnetics.frequency_domain_1d.options import (
    FDEM1DForwardOptions,
    FDEM1DInversionOptions,
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
from tests.utils.targets import (
    check_target,
    get_inversion_output,
)


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 638.1518041350254, "phi_d": 177000, "phi_m": 2860}


def test_fem_fwr_1d_run(
    tmp_path: Path,
    n_grid_points=3,
    refinement=(2,),
    cell_size=(20.0, 20.0, 20.0),
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="fdem 1d",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=10.0
        ),
        mesh=MeshOptions(
            cell_size=cell_size, refinement=refinement, padding_distance=400.0
        ),
        model=ModelOptions(background=1e-4, anomaly=0.1),
    )
    with Workspace.create(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5=geoh5, options=opts)
        params = FDEM1DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            z_real_channel_bool=True,
            z_imag_channel_bool=True,
        )

    fwr_driver = FDEM1DForwardDriver(params)
    fwr_driver.run()


def test_fem_1d_run(tmp_path: Path, max_iterations=1, pytest=True):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_fem_fwr_1d_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)
        data = {}
        uncertainties = {}
        channels = {
            "z_real": "z_real",
            "z_imag": "z_imag",
        }

        for chan, cname in channels.items():
            data[cname] = []
            uncertainties[f"{cname} uncertainties"] = []
            for ind, freq in enumerate(components.survey.channels):
                data_entity = geoh5.get_entity(f"Iteration_0_{chan}_[{ind}]")[0].copy(
                    parent=components.survey
                )
                data[cname].append(data_entity)
                abs_val = np.abs(data_entity.values)
                uncert = components.survey.add_data(
                    {
                        f"uncertainty_{chan}_[{ind}]": {
                            "values": np.ones_like(abs_val)
                            * freq
                            / 200.0  # * 2**(np.abs(ind-1))
                        }
                    }
                )
                uncertainties[f"{cname} uncertainties"].append(
                    uncert.copy(parent=components.survey)
                )

        data_groups = components.survey.add_components_data(data)
        uncert_groups = components.survey.add_components_data(uncertainties)

        data_kwargs = {}
        for chan, data_group, uncert_group in zip(
            channels, data_groups, uncert_groups, strict=True
        ):
            data_kwargs[f"{chan}_channel"] = data_group
            data_kwargs[f"{chan}_uncertainty"] = uncert_group

        orig_z_real_1 = geoh5.get_entity("Iteration_0_z_real_[0]")[0].values

        # Run the inverse
        params = FDEM1DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=1e-3,
            reference_model=1e-3,
            alpha_s=0.0,
            s_norm=0.0,
            x_norm=0.0,
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
        driver = FDEM1DInversionDriver(params)
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
    test_fem_fwr_1d_run(
        Path("./"), n_grid_points=5, cell_size=(5.0, 5.0, 5.0), refinement=(4, 4, 4)
    )
    test_fem_1d_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
