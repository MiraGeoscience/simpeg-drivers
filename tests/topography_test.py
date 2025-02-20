# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from pathlib import Path

import numpy as np

from simpeg_drivers.components import InversionTopography
from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.potential_fields import MVIInversionOptions
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def test_get_locations(tmp_path: Path):
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
    params = MVIInversionOptions(
        geoh5=geoh5,
        mesh=mesh,
        data_object=survey,
        tmi_channel=tmi_channel,
        active_cells=ActiveCellsOptions(
            topography_object=topography, topography=elevation
        ),
        starting_model=1.0,
    )
    geoh5 = params.geoh5
    topo = InversionTopography(geoh5, params)
    locs = topo.get_locations(params.active_cells.topography_object)
    np.testing.assert_allclose(
        locs[:, 2],
        params.active_cells.topography.values,
    )

    params.active_cells.topography = 199.0
    locs = topo.get_locations(params.active_cells.topography_object)
    np.testing.assert_allclose(locs[:, 2], np.ones_like(locs[:, 2]) * 199.0)
