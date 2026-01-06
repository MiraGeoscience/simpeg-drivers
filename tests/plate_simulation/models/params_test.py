# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Points, Surface

from simpeg_drivers.plate_simulation.models.options import PlateOptions


def test_plate_params(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
    params = PlateOptions(
        name="my plate",
        plate=1.0,
        width=20.0,
        strike_length=1500.0,
        dip_length=400.0,
        dip=90.0,
        dip_direction=0.0,
        reference="center",
        number=1,
        spacing=10.0,
        relative_locations=True,
        easting=10.0,
        northing=10.0,
        elevation=-100.0,
        reference_surface="topography",
        reference_type="mean",
    )
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
    assert np.allclose(center, [0, 0, -300])

    params.relative_locations = False
    center = params.center(survey, topography)
    assert np.allclose(center, [10, 10, -100])


def test_plate_params_empty_reference():
    params = PlateOptions(
        name="my plate",
        plate=1.0,
        width=20.0,
        strike_length=1500.0,
        dip_length=400.0,
        dip=90.0,
        dip_direction=0.0,
        reference="center",
        number=1,
        spacing=10.0,
        relative_locations=True,
        easting=10.0,
        northing=10.0,
        elevation=-100.0,
        reference_surface=None,
        reference_type=None,
    )
    assert params.reference_surface == "topography"
    assert params.reference_type == "mean"
