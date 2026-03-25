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

from simpeg_drivers.electricals.induced_polarization.two_dimensions import (
    IP2DForwardOptions,
    IP2DInversionOptions,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.driver import (
    IP2DForwardDriver,
    IP2DInversionDriver,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    DrapeModelOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.1244717397585979, "phi_d": 15500, "phi_m": 0.0002845}


def test_ip_2d_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
):
    # Run the forward
    opts = SyntheticsComponentsOptions(
        method="induced polarization 2d",
        survey=SurveyOptions(n_stations=n_electrodes, n_lines=n_lines),
        mesh=DrapeModelOptions(
            u_cell_size=5.0,
            v_cell_size=5.0,
            depth_core=50.0,
            expansion_factor=1.1,
            vertical_padding=200.0,
            horizontal_padding=200.0,
        ),
        model=ModelOptions(
            background=1e-6,
            anomaly=1e-1,
            plate=PlateModel(
                strike_length=1000.0,
                dip_length=50.0,
                width=20.0,
                origin=(0.0, 0.0, 0.0),
                direction=90,
                dip=45,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = IP2DForwardOptions.build(
            geoh5=geoh5,
            data_object=components.survey,
            mesh=components.mesh,
            topography_object=components.topography,
            starting_model=components.model,
            conductivity_model=1e2,
            model_type="Resistivity (Ohm-m)",
        )

    fwr_driver = IP2DForwardDriver(params)
    fwr_driver.run()


def test_ip_2d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_ip_2d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)
        chargeability = geoh5.get_entity("Iteration_0_chargeability")[0]
        uncertainties = chargeability.parent.add_data(
            {
                "Uncertainties": {
                    "values": np.abs(chargeability.values) * 0.05 + 1e-4,
                }
            }
        )
        # Run the inverse without a mesh
        params = IP2DInversionOptions.build(
            geoh5=geoh5,
            topography_object=components.topography,
            drape_model=DrapeModelOptions(
                u_cell_size=5.0,
                v_cell_size=5.0,
                depth_core=50.0,
                expansion_factor=1.1,
                vertical_padding=200.0,
                horizontal_padding=200.0,
            ),
            data_object=chargeability.parent,
            chargeability_channel=chargeability,
            chargeability_uncertainty=uncertainties,
            starting_model=1e-6,
            reference_model=1e-6,
            conductivity_model=1e-2,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-2,
            percentile=100,
            upper_bound=0.1,
            cooling_rate=1,
        )
        # TODO Fix the write out with Multiselect of ReferenceData values
        # params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = IP2DInversionDriver(params)
    driver.run()
    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = chargeability.values[np.isfinite(chargeability.values)]
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_ip_2d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=3,
    )
    test_ip_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
