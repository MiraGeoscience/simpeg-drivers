# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
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

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Points
from octree_creation_app.driver import OctreeDriver
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import gaussian_filter

from simpeg_drivers.utils.meshes import auto_mesh_parameters, auto_pad
from tests.utils_surveys_test import create_test_survey


def generate_random_topography(
    survey: np.ndarray, drape_survey: float | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate random topography over the survey area with optional drape.

    :param survey: Array of survey locations.
    :param drape_survey: If not none, the survey z values will be replaced with
        an interpolation of the topography and shifted by the provided value.
    """

    xmin = survey[:, 0].min()
    xmax = survey[:, 0].max()
    ymin = survey[:, 1].min()
    ymax = survey[:, 1].max()
    xrange = xmax - xmin
    yrange = ymax - ymin

    topo_x = np.linspace(xmin - 0.5 * xrange, xmax + 0.5 * xrange, 100)
    topo_y = np.linspace(ymin - 0.5 * yrange, ymax + 0.5 * yrange, 100)
    topo_grid_x, topo_grid_y = np.meshgrid(topo_x, topo_y)

    elevs = 200 * np.random.randn(topo_grid_x.shape[0], topo_grid_x.shape[1])
    elevs = gaussian_filter(elevs, 2)

    topo = np.c_[topo_grid_x.flatten(), topo_grid_y.flatten(), elevs.flatten()]

    if drape_survey is not None:
        interp = LinearNDInterpolator(topo[:, :2], topo[:, 2])
        survey[:, 2] = interp(survey[:, :2]) + drape_survey

    return survey, topo


def test_auto_pad():
    x = np.linspace(0, 1000, 101)
    y = np.linspace(0, 500, 501)
    x_grid, y_grid = np.meshgrid(x, y)
    z = np.ones_like(x_grid)
    survey = np.c_[x_grid.flatten(), y_grid.flatten(), z.flatten()]
    horizontal_padding, vertical_padding = auto_pad(survey)
    assert horizontal_padding == [500, 500, 500, 500]
    assert vertical_padding == [500, 500]


def test_auto_mesh_parameters(tmp_path):
    ws = Workspace(tmp_path / "test.geoh5")
    locs = create_test_survey()
    locs, topo = generate_random_topography(locs, drape_survey=0)

    survey = Points.create(ws, name="survey", vertices=locs)
    topo = Points.create(ws, name="topography", vertices=topo)

    params = auto_mesh_parameters(survey, topo)
    mesh = OctreeDriver.octree_from_params(params)

    assert mesh.u_cell_size == 10
    assert mesh.v_cell_size == 10
    assert mesh.w_cell_size == 10
    assert True
    # TODO make sense of the padding and add an assertion
