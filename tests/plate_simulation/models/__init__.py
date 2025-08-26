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
from geoh5py.objects import Surface
from grid_apps.octree_creation.driver import OctreeDriver
from grid_apps.octree_creation.options import OctreeOptions


def get_topo_mesh(workspace):
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0],
            [10.0, 10.0, 0.0],
            [0.0, 10.0, 0.0],
        ]
    )
    cells = np.array([[0, 1, 2], [0, 2, 3]])

    topography = Surface.create(workspace, name="topo", vertices=vertices, cells=cells)

    kwargs = {
        "geoh5": workspace,
        "objects": topography,
        "u_cell_size": 0.5,
        "v_cell_size": 0.5,
        "w_cell_size": 0.5,
        "horizontal_padding": 10.0,
        "vertical_padding": 10.0,
        "depth_core": 5.0,
        "minimum_level": 4,
        "diagonal_balance": False,
        "refinements": [
            {
                "refinement_object": topography,
                "levels": [4, 2, 1],
                "horizon": True,
            }
        ],
    }
    params = OctreeOptions(**kwargs)
    params.write_ui_json(workspace.h5file.parent / "octree.ui.json")
    driver = OctreeDriver(params)
    octree = driver.run()
    return topography, octree
