# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                     '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np

from simpeg_drivers.components import InversionTopography
from simpeg_drivers.potential_fields import MagneticVectorParams
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


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

    geotest = Geoh5Tester(geoh5, tmp_path, "test.geoh5", MagneticVectorParams)
    geotest.set_param("mesh", str(mesh.uid))
    geotest.set_param("data_object", str(survey.uid))
    geotest.set_param("tmi_channel", str(tmi_channel.uid))
    geotest.set_param("topography_object", str(topography.uid))
    geotest.set_param("topography", str(elevation.uid))
    return geotest.make()


def test_get_locations(tmp_path: Path):
    ws, params = setup_params(tmp_path)
    topo = InversionTopography(ws, params)
    locs = topo.get_locations(params.topography_object)
    np.testing.assert_allclose(
        locs[:, 2],
        params.topography.values,
    )

    params.topography = 199.0
    locs = topo.get_locations(params.topography_object)
    np.testing.assert_allclose(locs[:, 2], np.ones_like(locs[:, 2]) * 199.0)
