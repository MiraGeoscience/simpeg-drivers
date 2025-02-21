# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import numpy as np

from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.potential_fields import GravityInversionOptions
from simpeg_drivers.potential_fields.gravity.driver import GravityInversionDriver
from simpeg_drivers.utils.testing import setup_inversion_workspace


def test_smallness_terms(tmp_path: Path):
    n_grid_points = 2
    refinement = (2,)

    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.75,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        refinement=refinement,
        flatten=False,
    )

    gz = survey.add_data({"gz": {"values": np.ones(survey.n_vertices)}})
    mesh = model.parent
    active_cells = ActiveCellsOptions(topography_object=topography)
    params = GravityInversionOptions(
        geoh5=geoh5,
        mesh=mesh,
        active_cells=active_cells,
        data_object=gz.parent,
        starting_model=1e-4,
        reference_model=0.0,
        alpha_s=1.0,
        s_norm=0.0,
        gradient_type="components",
        gz_channel_bool=True,
        gz_channel=gz,
        gz_uncertainty=2e-3,
        lower_bound=0.0,
        max_global_iterations=1,
        initial_beta_ratio=1e-2,
        prctile=100,
        store_sensitivities="ram",
    )
    params.alpha_s = None
    driver = GravityInversionDriver(params)
    assert driver.regularization.objfcts[0].alpha_s == 0.0
