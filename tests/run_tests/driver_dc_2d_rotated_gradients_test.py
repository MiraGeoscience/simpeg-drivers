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
from geoh5py.groups import PropertyGroup
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.direct_current.two_dimensions.driver import (
    DC2DForwardDriver,
    DC2DInversionDriver,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.options import (
    DC2DForwardOptions,
    DC2DInversionOptions,
)
from simpeg_drivers.options import (
    DrapeModelOptions,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import check_target, get_inversion_output, get_workspace


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 10.305373769233688, "phi_d": 187000, "phi_m": 410}


def test_dc_rotated_2d_fwr_run(tmp_path: Path, n_electrodes=10, n_lines=3):
    opts = SyntheticsComponentsOptions(
        method="direct current 2d",
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
            background=0.001,
            anomaly=1.0,
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
        params = DC2DForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
        )
    fwr_driver = DC2DForwardDriver(params)
    fwr_driver.run()


def test_dc_rotated_gradient_2d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = (
            tmp_path.parent / "test_dc_rotated_2d_fwr_run0" / "inversion_test.ui.geoh5"
        )

    with Workspace(workpath) as geoh5:
        components = SyntheticsComponents(geoh5)

        fwr_group = geoh5.get_entity("Direct Current 2D Forward")[0]
        survey = fwr_group.get_entity("survey")[0]
        potential = survey.get_data("Iteration_0_potential")[0]
        uncertainties = survey.add_data(
            {
                "Uncertainties": {
                    "values": np.abs(potential.values) * 0.05 + 1e-4,
                }
            }
        )
        # Create property group with orientation
        dip = np.ones(components.mesh.n_cells) * 45
        azimuth = np.ones(components.mesh.n_cells) * 90

        data_list = components.mesh.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            components.mesh,
            properties=data_list,
            property_group_type="Dip direction & dip",
        )

        # Run the inverse
        params = DC2DInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=potential.parent,
            gradient_rotation=pg,
            potential_channel=potential,
            potential_uncertainty=uncertainties,
            starting_model=1e-3,
            reference_model=1e-3,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            length_scale_z=0.1,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=10.0,
            percentile=100,
            upper_bound=10,
            cooling_rate=1,
            sens_wts_threshold=1.0,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = DC2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_dc_rotated_2d_fwr_run(Path("./"), n_electrodes=20, n_lines=3)
    test_dc_rotated_gradient_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
