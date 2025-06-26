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
from geoh5py.objects import Points, Surface


def get_survey(workspace, n_receivers, n_lines):
    X, Y = np.meshgrid(  # pylint: disable=invalid-name
        np.linspace(-250, 250, n_receivers), np.linspace(-250, 250, n_lines)
    )
    Z = np.zeros_like(X)  # pylint: disable=invalid-name

    vertices = np.c_[X.T.flatten(), Y.T.flatten(), Z.T.flatten()]

    return Points.create(
        workspace,
        vertices=vertices,
        name="survey",
    )


def get_topography(workspace):
    vertices = np.array(
        [
            [-500.0, -500.0, 0.0],
            [500.0, -500.0, 0.0],
            [500.0, 500.0, 0.0],
            [-500.0, 500.0, 0.0],
        ]
    )
    cells = np.array([[0, 1, 2], [0, 2, 3]])

    return Surface.create(workspace, name="topo", vertices=vertices, cells=cells)
