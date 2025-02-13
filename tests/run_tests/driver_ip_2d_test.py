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
from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.induced_polarization.two_dimensions import (
    IP2DForwardParams,
    IP2DInversionParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.driver import (
    IP2DForwardDriver,
    IP2DInversionDriver,
)
from simpeg_drivers.electricals.params import DrapeModelData, LineSelectionData
from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.09052544, "phi_d": 24910, "phi_m": 0.1845}


def test_ip_2d_fwr_run(
    tmp_path: Path,
    n_electrodes=10,
    n_lines=3,
    refinement=(4, 6),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=1e-6,
        anomaly=1e-1,
        n_electrodes=n_electrodes,
        n_lines=n_lines,
        refinement=refinement,
        inversion_type="dcip_2d",
        flatten=False,
        drape_height=0.0,
    )
    params = IP2DForwardParams(
        geoh5=geoh5,
        data_object=survey,
        mesh=model.parent,
        active_cells=ActiveCellsData(topography_object=topography),
        z_from_topo=True,
        starting_model=model,
        conductivity_model=1e-2,
        line_selection=LineSelectionData(
            line_object=geoh5.get_entity("line_ids")[0],
            line_id=101,
        ),
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
        chargeability = geoh5.get_entity("Iteration_0_ip")[0]
        mesh = geoh5.get_entity("Models")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = IP2DInversionParams(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=ActiveCellsData(topography_object=topography),
            data_object=chargeability.parent,
            chargeability_channel=chargeability,
            chargeability_uncertainty=2e-4,
            line_selection=LineSelectionData(
                line_object=geoh5.get_entity("line_ids")[0],
                line_id=101,
            ),
            starting_model=1e-6,
            reference_model=1e-6,
            conductivity_model=1e-2,
            s_norm=0.0,
            x_norm=0.0,
            z_norm=0.0,
            gradient_type="components",
            z_from_topo=True,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            prctile=100,
            upper_bound=0.1,
            store_sensitivities="ram",
            coolingRate=1,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = IP2DInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

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
        refinement=(4, 8),
    )
    test_ip_2d_run(
        Path("./"),
        max_iterations=20,
        pytest=False,
    )
