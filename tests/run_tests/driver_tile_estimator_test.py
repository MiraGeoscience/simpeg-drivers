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
from geoh5py import Workspace

from simpeg_drivers.potential_fields import MagneticInversionOptions
from simpeg_drivers.potential_fields.magnetic_scalar.driver import (
    MagneticInversionDriver,
)
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from simpeg_drivers.utils.tile_estimate import TileEstimator, TileParameters
from simpeg_drivers.utils.utils import simpeg_group_to_driver


def test_tile_estimator_run(
    tmp_path: Path,
    n_grid_points=16,
    refinement=(2,),
):
    inducing_field = (49999.8, 90.0, 0.0)
    # Run the forward

    opts = SyntheticsComponentsOptions(
        method="magnetic_scalar",
        survey=SurveyOptions(n_stations=n_grid_points, n_lines=n_grid_points),
        mesh=MeshOptions(refinement=refinement),
        model=ModelOptions(anomaly=0.05),
    )
    with Workspace.create(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        tmi_channel = components.survey.add_data(
            {
                "tmi": {"values": np.random.rand(components.survey.n_vertices)},
            }
        )
        params = MagneticInversionOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            data_object=components.survey,
            tmi_channel=tmi_channel,
            starting_model=components.model,
        )

    driver = MagneticInversionDriver(params)
    tile_params = TileParameters(geoh5=geoh5, simulation=driver.out_group)
    estimator = TileEstimator(tile_params)

    assert len(estimator.get_results(max_tiles=32)) == 8

    with geoh5.open():
        simpeg_group = estimator.run()
        driver = simpeg_group_to_driver(simpeg_group, geoh5)

    assert driver.inversion_type == "magnetic scalar"
    assert driver.params.compute.tile_spatial == 2
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
