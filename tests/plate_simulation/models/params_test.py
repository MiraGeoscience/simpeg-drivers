# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import logging

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py import Workspace
from geoh5py.objects import Points, Surface

from simpeg_drivers.plate_simulation.models.options import PlateOptions
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
from simpeg_drivers.utils.synthetics.options import (
    SurveyOptions,
    SyntheticsComponentsOptions,
)


def test_plate_options_center(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as workspace:
        components = SyntheticsComponents(
            geoh5=workspace,
            options=SyntheticsComponentsOptions(
                method="gravity",
                refine_plate=True,
                survey=SurveyOptions(
                    center=(0.0, 0.0), n_stations=10, n_lines=10, drape=15.0
                ),
            ),
        )

        params = PlateOptions(
            name="my plate",
            plate_property=1.0,
            geometry=PlateModel(
                strike_length=40.0,
                dip_length=80.0,
                width=5.0,
                easting=10.0,
                northing=-10.0,
                elevation=30.0,
                direction=0.0,
                dip=90.0,
            ),
            number=1,
            spacing=10.0,
        )
        center = params.center(components.survey, components.topography)
        assert np.allclose(center, [0.0, 0.0, 20], atol=7e-1)


def test_plate_params(tmp_path, caplog):
    workspace = Workspace(tmp_path / "test.geoh5")
    with caplog.at_level(logging.WARNING):
        params = PlateOptions(
            name="my plate",
            plate_property=1.0,
            geometry=PlateModel(
                strike_length=1500.0,
                dip_length=400.0,
                width=20.0,
                easting=10.0,
                northing=10.0,
                elevation=100.0,
                direction=0.0,
                dip=90.0,
            ),
            number=1,
            spacing=10.0,
            relative_locations=False,
        )
    assert "'relative_locations' will be ignored" in caplog.text
    assert params.spacing == 0.0

    survey = Points.create(
        workspace,
        name="survey",
        vertices=np.array([[-10, -10, 0]]),
    )
    topography = Surface.create(
        workspace,
        name="test",
        vertices=np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]]),
        cells=np.array([[0, 1, 2], [0, 2, 3]]),
    )

    center = params.center(survey, topography)
    assert np.allclose(center, [-10.0, -10.0, -100])
