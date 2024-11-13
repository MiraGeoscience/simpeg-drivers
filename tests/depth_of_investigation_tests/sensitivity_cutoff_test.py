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
from octree_creation_app.params import OctreeParams

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver import (
    SensitivityCutoffDriver,
    scale_sensitivity,
)
from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.params import (
    SensitivityCutoffParams,
)


def generate_sensitivity(workspace: Workspace, depth_scaling=False):
    x = np.linspace(-500, 500, 21)
    y = np.array([-200, -100, 0, 100, 200])
    x_grid, y_grid = np.meshgrid(x, y)
    vertices = np.c_[
        x_grid.flatten(), y_grid.flatten(), np.zeros_like(x_grid.flatten())
    ]
    survey = Points.create(workspace, name="survey", vertices=vertices)
    refinements = {
        "Refinement A object": survey,
        "Refinement A levels": "4, 4, 4",
        "Refinement A horizon": False,
    }
    octree_params = OctreeParams(
        geoh5=workspace,
        objects=survey,
        u_cell_size=25,
        v_cell_size=25,
        w_cell_size=25,
        padding_distance=1000,
        depth_core=500,
        minimum_level=4,
        diagonal_balance=True,
        **refinements,
    )
    mesh = OctreeDriver.octree_from_params(octree_params)

    values = (
        mesh.octree_cells["NCells"]
        * mesh.u_cell_size
        * mesh.octree_cells["NCells"]
        * mesh.v_cell_size
        * mesh.octree_cells["NCells"]
        * mesh.w_cell_size
    )

    if depth_scaling:
        z = mesh.centroids[:, 2]
        z += np.abs(z.min())
        values *= z
        # depths = z.max() - z + 100
        # values /= depths

    sensitivity = mesh.add_data(
        {"sensitivity": {"association": "Cell", "values": values}}
    )
    return sensitivity


def test_scale_sensitivity(tmp_path):
    ws = Workspace(tmp_path / "test.geoh5")
    sensitivity = generate_sensitivity(ws)
    validation = scale_sensitivity(sensitivity)

    assert np.allclose(validation, 100 * np.ones_like(validation))


def test_driver(tmp_path):
    """
    Idea:

    The sensitivity we use scales with elevation and cell size. The program
    rescales the sensitivities to remove the cell size bias leaving the just
    the elvation dependence. With a 10% cutoff, we can predict that the mask
    will remove the cells with the lowest 10% of elevations.
    """

    ws = Workspace(tmp_path / "test.geoh5")
    sensitivity = generate_sensitivity(ws, depth_scaling=True)
    mesh = sensitivity.parent
    params = SensitivityCutoffParams(
        geoh5=mesh.workspace,
        mesh=mesh,
        sensitivity_model=sensitivity,
        sensitivity_cutoff=10,
    )
    driver = SensitivityCutoffDriver(params)
    mask = driver.run()

    z = mesh.centroids[:, 2]
    z_range = z.max() - z.min()
    depth_cutoff = z.min() + (z_range * 0.1)
    depth_mask = z >= depth_cutoff
    mesh.add_data({"depth_mask": {"association": "Cell", "values": depth_mask}})
    assert np.allclose(depth_mask, mask.values)
