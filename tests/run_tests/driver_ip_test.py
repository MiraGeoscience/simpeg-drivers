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

from __future__ import annotations

from pathlib import Path

from geoh5py.workspace import Workspace

from simpeg_drivers.electricals.induced_polarization.three_dimensions import (
    InducedPolarization3DParams,
)
from simpeg_drivers.electricals.induced_polarization.three_dimensions.driver import (
    InducedPolarization3DDriver,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output

# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.008494, "phi_d": 1.438, "phi_m": 0.3258}


def test_ip_3d_fwr_run(
    tmp_path: Path,
    n_electrodes=4,
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
        drape_height=0.0,
        inversion_type="dcip",
        flatten=False,
    )
    params = InducedPolarization3DParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        z_from_topo=True,
        data_object=survey.uid,
        starting_model=model.uid,
        conductivity_model=1e-2,
    )
    params.workpath = tmp_path
    fwr_driver = InducedPolarization3DDriver(params)
    fwr_driver.run()


def test_ip_3d_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
    n_lines=3,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_ip_3d_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        potential = geoh5.get_entity("Iteration_0_ip")[0]
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        params = InducedPolarization3DParams(
            geoh5=geoh5,
            mesh=mesh.uid,
            topography_object=topography.uid,
            data_object=potential.parent.uid,
            conductivity_model=1e-2,
            reference_model=1e-6,
            starting_model=1e-6,
            s_norm=0.0,
            x_norm=0.0,
            y_norm=0.0,
            z_norm=0.0,
            gradient_type="components",
            chargeability_channel_bool=True,
            z_from_topo=False,
            chargeability_channel=potential.uid,
            chargeability_uncertainty=2e-4,
            max_global_iterations=max_iterations,
            initial_beta=None,
            initial_beta_ratio=1e0,
            prctile=100,
            upper_bound=0.1,
            tile_spatial=n_lines,
            store_sensitivities="ram",
            coolingRate=1,
        )
        params.write_input_file(path=tmp_path, name="Inv_run")
    driver = InducedPolarization3DDriver.start(str(tmp_path / "Inv_run.ui.json"))

    output = get_inversion_output(
        driver.params.geoh5.h5file, driver.params.out_group.uid
    )
    if geoh5.open():
        output["data"] = potential.values
    if pytest:
        check_target(output, target_run)


if __name__ == "__main__":
    # Full run
    test_ip_3d_fwr_run(
        Path("./"),
        n_electrodes=20,
        n_lines=5,
        refinement=(4, 8),
    )
    test_ip_3d_run(
        Path("./"),
        n_lines=5,
        max_iterations=15,
        pytest=False,
    )
