# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Octree, Points
from grid_apps.octree_creation.driver import OctreeDriver
from grid_apps.octree_creation.options import OctreeOptions, RefinementOptions

from simpeg_drivers.utils.utils import mask_vertices_and_cells, octree_extents


def test_octree_extents(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as ws:
        X, Y = np.meshgrid(np.linspace(0, 1000, 51), np.linspace(0, 1000, 51))
        Z = np.zeros_like(X)
        vertices = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
        pts = Points.create(ws, name="points", vertices=vertices)
        options = OctreeOptions(
            geoh5=ws,
            objects=pts,
            refinements=[
                RefinementOptions(
                    refinement_object=pts, levels=[4, 2], horizon=False, distance=100
                ),
            ],
        )
        octree = OctreeDriver.octree_from_params(options)

    extents = octree_extents(octree)
    assert np.allclose(extents, [-1112.5, 2087.5, -1112.5, 2087.5, -1062.5, 537.5])


def test_mask_vertices_and_cells():
    X, Y = np.meshgrid(np.arange(3), np.arange(3))
    Z = np.zeros_like(X)
    vertices = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    cells = np.array(
        [
            [0, 1, 3],
            [3, 1, 4],
            [1, 2, 4],
            [4, 2, 5],
            [3, 4, 6],
            [6, 4, 7],
            [4, 5, 7],
            [7, 5, 8],
        ]
    )
    extent = [0.5, 2, 0, 2, 0, 1]
    masked_vertices, masked_cells = mask_vertices_and_cells(extent, vertices, cells)
    assert len(masked_vertices) == len(vertices)
    assert len(masked_cells) == len(cells)
    extent = [1.5, 2, 0, 2, 0, 1]
    masked_vertices, masked_cells = mask_vertices_and_cells(extent, vertices, cells)
    assert len(masked_vertices) == 6
    assert len(masked_cells) == 4
