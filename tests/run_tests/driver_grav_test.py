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
from unittest.mock import patch

import numpy as np
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.workspace import Workspace
from pytest import raises

from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.potential_fields import (
    GravityForwardOptions,
    GravityInversionOptions,
)
from simpeg_drivers.potential_fields.gravity.driver import (
    GravityForwardDriver,
    GravityInversionDriver,
)
from simpeg_drivers.utils.testing import check_target, setup_inversion_workspace
from simpeg_drivers.utils.utils import get_inversion_output


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 0.0028055269276044915, "phi_d": 8.315e-05, "phi_m": 0.002882}


def test_gravity_fwr_run(
    tmp_path: Path,
    n_grid_points=2,
    refinement=(2,),
):
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.75,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        flatten=False,
    )

    active_cells = ActiveCellsOptions(topography_object=topography)
    params = GravityForwardOptions(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=active_cells,
        topography_object=topography,
        data_object=survey,
        starting_model=model,
        gz_channel_bool=True,
    )
    fwr_driver = GravityForwardDriver(params)
    fwr_driver.run()


def test_array_too_large_run(
    tmp_path: Path,
):
    workpath = tmp_path.parent / "test_gravity_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        gz = geoh5.get_entity("Iteration_0_gz")[0]
        mesh = geoh5.get_entity("mesh")[0]
        topography = geoh5.get_entity("topography")[0]

        # Run the inverse
        active_cells = ActiveCellsOptions(topography_object=topography)
        params = GravityInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=active_cells,
            data_object=gz.parent,
            gz_channel=gz,
            gz_uncertainty=1e-4,
            starting_model=1e-4,
        )

    with patch(
        "simpeg.inversion.BaseInversion.run",
        side_effect=np.core._exceptions._ArrayMemoryError((0,), np.dtype("float64")),  # pylint: disable=protected-access
    ):
        with raises(GeoAppsError, match="Memory Error"):
            driver = GravityInversionDriver(params)
            driver.run()


def test_gravity_run(
    tmp_path: Path,
    max_iterations=1,
    pytest=True,
):
    workpath = tmp_path / "inversion_test.ui.geoh5"
    if pytest:
        workpath = tmp_path.parent / "test_gravity_fwr_run0" / "inversion_test.ui.geoh5"

    with Workspace(workpath) as geoh5:
        gz = geoh5.get_entity("Iteration_0_gz")[0]
        orig_gz = gz.values.copy()
        mesh = geoh5.get_entity("mesh")[0]
        model = mesh.get_entity("starting_model")[0]

        inds = (mesh.centroids[:, 0] > -35) & (mesh.centroids[:, 0] < 35)
        norms = np.ones(mesh.n_cells) * 2
        norms[inds] = 0
        gradient_norms = mesh.add_data({"norms": {"values": norms}})

        # Test mesh UBC ordered
        ind = np.argsort(mesh.octree_cells, order=["K", "J", "I"])
        mesh.octree_cells = mesh.octree_cells[ind]
        model.values = model.values[ind]
        gradient_norms.values = gradient_norms.values[ind]

        topography = geoh5.get_entity("topography")[0]

        # Turn some values to nan
        values = gz.values.copy()
        values[0] = np.nan
        gz.values = values

        # Run the inverse
        active_cells = ActiveCellsOptions(topography_object=topography)
        params = GravityInversionOptions(
            geoh5=geoh5,
            mesh=mesh,
            active_cells=active_cells,
            data_object=gz.parent,
            starting_model=1e-4,
            reference_model=0.0,
            s_norm=0.0,
            x_norm=gradient_norms,
            y_norm=gradient_norms,
            z_norm=gradient_norms,
            gradient_type="components",
            gz_channel=gz,
            gz_uncertainty=2e-3,
            lower_bound=0.0,
            max_global_iterations=max_iterations,
            initial_beta_ratio=1e-2,
            prctile=100,
            store_sensitivities="ram",
            save_sensitivities=True,
        )
        params.write_ui_json(path=tmp_path / "Inv_run.ui.json")

    driver = GravityInversionDriver.start(str(tmp_path / "Inv_run.ui.json"))

    assert driver.params.data_object.uid != gz.parent.uid
    assert driver.models.upper_bound is np.inf

    with Workspace(driver.params.geoh5.h5file) as run_ws:
        output = get_inversion_output(
            driver.params.geoh5.h5file, driver.params.out_group.uid
        )

        residual = run_ws.get_entity("Iteration_1_gz_Residual")[0]
        assert np.isnan(residual.values).sum() == 1, "Number of nan residuals differ."

        predicted = next(
            pred
            for pred in run_ws.get_entity("Iteration_0_gz")
            if pred.parent.parent.name == "Gravity Inversion"
        )
        assert not any(np.isnan(predicted.values)), (
            "Predicted data should not have nans."
        )
        output["data"] = orig_gz

        assert len(run_ws.get_entity("SimPEG.log")) == 2

        if pytest:
            check_target(output, target_run)
            nan_ind = np.isnan(run_ws.get_entity("Iteration_0_model")[0].values)
            inactive_ind = run_ws.get_entity("active_cells")[0].values == 0
            assert np.all(nan_ind == inactive_ind)


if __name__ == "__main__":
    # Full run
    test_gravity_fwr_run(
        Path("./"),
        n_grid_points=20,
        refinement=(4, 8),
    )

    test_gravity_run(
        Path("./"),
        max_iterations=15,
        pytest=False,
    )
