#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of geoapps.
#
#  geoapps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).


from __future__ import annotations

from pathlib import Path

import numpy as np
from discretize import TreeMesh

from simpeg_drivers.components import InversionData, InversionMesh, InversionTopography
from simpeg_drivers.potential_fields import MagneticVectorParams
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace
from tests import GEOH5 as geoh5


def setup_params(tmp_path):
    geoh5, entity, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=(2,),
        n_electrodes=2,
        n_lines=2,
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
