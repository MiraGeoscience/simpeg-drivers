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

import numpy as np
import pytest
from discretize import TreeMesh
from geoh5py import Workspace
from geoh5py.objects import Octree
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree

from simpeg_drivers.components import InversionData, InversionMesh, InversionTopography
from simpeg_drivers.potential_fields import MagneticVectorParams
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def setup_params(tmp_path):
    geoh5, entity, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=(2,),
        n_electrodes=4,
        n_lines=4,
        inversion_type="magnetic_vector",
    )

    mesh = model.parent

    tmi_channel, gyz_channel = survey.add_data(
        {
            "tmi": {"values": np.random.rand(survey.n_vertices)},
            "gyz": {"values": np.random.rand(survey.n_vertices)},
        }
    )
    elevation = topography.add_data(
        {"elevation": {"values": topography.vertices[:, 2]}}
    )
    elevation = topography.children[0]
    geotest = Geoh5Tester(geoh5, tmp_path, "test.geoh5", MagneticVectorParams)
    geotest.set_param("mesh", str(mesh.uid))
    geotest.set_param("data_object", str(survey.uid))
    geotest.set_param("topography_object", str(topography.uid))
    geotest.set_param("tmi_channel", str(tmi_channel.uid))
    geotest.set_param("topography", str(elevation.uid))
    return geotest.make()


def test_initialize(tmp_path: Path):
    ws, params = setup_params(tmp_path)
    inversion_data = InversionData(ws, params)
    inversion_topography = InversionTopography(ws, params)
    inversion_mesh = InversionMesh(ws, params, inversion_data, inversion_topography)
    assert isinstance(inversion_mesh.mesh, TreeMesh)


def test_ensure_cell_convention(tmp_path):
    workspace = Workspace(tmp_path / "test_octree.geoh5")
    octree_cells = np.array(
        [
            (0, 0, 0, 1),
            (1, 0, 0, 1),
            (0, 1, 0, 1),
            (1, 1, 0, 1),
            (0, 0, 1, 1),
            (1, 0, 1, 1),
            (0, 1, 1, 1),
            (1, 1, 1, 1),
        ],
        dtype=[("I", "<i4"), ("J", "<i4"), ("K", "<i4"), ("NCells", "<i4")],
    )
    test_mesh = Octree.create(
        workspace,
        name="Mesh",
        origin=np.array([0, 0, 10]),
        u_count=2,
        v_count=2,
        w_count=2,
        u_cell_size=5.0,
        v_cell_size=5.0,
        w_cell_size=-5.0,
        octree_cells=octree_cells,
    )

    validation_mesh = test_mesh.copy()
    validation_mesh.name = "validation"
    old_centroids = test_mesh.centroids.copy()
    treemesh = InversionMesh.ensure_cell_convention(test_mesh)
    test_mesh = treemesh_2_octree(workspace, treemesh)
    new_centroids = test_mesh.centroids.copy()
    assert np.allclose(np.sort(old_centroids.flat), np.sort(new_centroids.flat))


def test_is_conventional(tmp_path):
    workspace = Workspace(tmp_path / "test_octree.geoh5")

    # Positive cells sizes and IJK ordering
    cells = np.array(
        [
            [0, 0, 0, 1],
            [1, 0, 0, 1],
            [0, 1, 0, 1],
            [1, 1, 0, 1],
            [0, 0, 1, 1],
            [1, 0, 1, 1],
            [0, 1, 1, 1],
            [1, 1, 1, 1],
        ]
    )
    octree = Octree.create(
        workspace,
        u_count=2,
        v_count=2,
        w_count=2,
        u_cell_size=1.,
        v_cell_size=1.,
        w_cell_size=1.,
        octree_cells=cells,
        name="All is well",
    )
    assert InversionMesh.is_conventional(octree)

    # Z ordering
    cells = np.array(
        [
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 1, 0, 1],
            [0, 1, 1, 1],
            [1, 0, 0, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 1],
        ]
    )
    octree = Octree.create(
        workspace,
        u_count=2,
        v_count=2,
        w_count=2,
        u_cell_size=1,
        v_cell_size=1,
        w_cell_size=1,
        octree_cells=cells,
        name="Uh oh",
    )
    assert not InversionMesh.is_conventional(octree)

    # Negative cell sizes
    cells = np.array(
        [
            [0, 0, 1, 1],
            [1, 0, 1, 1],
            [0, 1, 1, 1],
            [1, 1, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1],
            [0, 1, 0, 1],
            [1, 1, 0, 1],
        ]
    )
    octree = Octree.create(
        workspace,
        u_count=2,
        v_count=2,
        w_count=2,
        u_cell_size=1,
        v_cell_size=1,
        w_cell_size=-1,
        octree_cells=cells,
        name="All is well",
    )
    assert not InversionMesh.is_conventional(octree)


def test_raise_on_rotated_negative_cell_size(tmp_path):
    ws, params = setup_params(tmp_path)
    mesh = params.mesh
    mesh.rotation = 20.0
    mesh.w_cell_size *= -1
    msg = "Cannot convert negative cell sizes for rotated mesh."
    with pytest.raises(ValueError, match=msg):
        InversionMesh.ensure_cell_convention(mesh)
