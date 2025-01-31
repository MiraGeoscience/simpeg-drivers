# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2025 Mira Geoscience Ltd.                                     '
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

from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.potential_fields import MagneticScalarInversionParams
from simpeg_drivers.potential_fields.magnetic_scalar.driver import (
    MagneticScalarInversionDriver,
)
from simpeg_drivers.utils.testing import setup_inversion_workspace
from simpeg_drivers.utils.tile_estimate import TileEstimator, TileParameters
from simpeg_drivers.utils.utils import simpeg_group_to_driver


def test_tile_estimator_run(
    tmp_path: Path,
    n_grid_points=16,
    refinement=(2,),
):
    inducing_field = (49999.8, 90.0, 0.0)
    # Run the forward
    geoh5, _, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=refinement,
        n_electrodes=n_grid_points,
        n_lines=n_grid_points,
        flatten=False,
    )
    tmi_channel = survey.add_data(
        {
            "tmi": {"values": np.random.rand(survey.n_vertices)},
        }
    )
    params = MagneticScalarInversionParams(
        geoh5=geoh5,
        mesh=model.parent,
        active_cells=ActiveCellsData(topography_object=topography),
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        z_from_topo=False,
        data_object=survey,
        tmi_channel=tmi_channel,
        starting_model=model,
    )

    driver = MagneticScalarInversionDriver(params)
    tile_params = TileParameters(geoh5=geoh5, simulation=driver.out_group)
    estimator = TileEstimator(tile_params)

    assert len(estimator.get_results(max_tiles=32)) == 8

    simpeg_group = estimator.run()

    driver = simpeg_group_to_driver(simpeg_group, geoh5)

    assert driver.inversion_type == "magnetic scalar"
    assert driver.params.tile_spatial == 2
    assert (
        len(simpeg_group.children) == 2
        and simpeg_group.children[0].name == "tile_estimator.png"
    )


def test_optimal_tile_size():
    tile = 10.0 ** np.arange(-1, 1, 0.25)
    size = 1.0 / tile
    results = dict(zip(tile, size, strict=False))
    optimal = TileEstimator.estimate_optimal_tile(results)

    assert optimal == 1
