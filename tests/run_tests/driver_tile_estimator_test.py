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

from simpeg_drivers.potential_fields import MagneticScalarParams
from simpeg_drivers.potential_fields.magnetic_scalar.driver import MagneticScalarDriver
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
    params = MagneticScalarParams(
        forward_only=True,
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        z_from_topo=False,
        data_object=survey.uid,
        starting_model=model.uid,
    )
    params.workpath = tmp_path

    driver = MagneticScalarDriver(params)
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
