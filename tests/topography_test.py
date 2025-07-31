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

from simpeg_drivers.components import InversionData, InversionMesh, InversionTopography
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import MVIInversionOptions
from simpeg_drivers.utils.testing_utils.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticDataInversionOptions,
)
from simpeg_drivers.utils.testing_utils.runtests import setup_inversion_workspace


def test_get_locations(tmp_path: Path):
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(n_stations=2, n_lines=2),
        mesh=MeshOptions(refinement=(2,)),
        model=ModelOptions(anomaly=0.05),
    )
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="magnetic_vector", options=opts
    )
    with geoh5.open():
        tmi_channel, gyz_channel = survey.add_data(
            {
                "tmi": {"values": np.random.rand(survey.n_vertices)},
                "gyz": {"values": np.random.rand(survey.n_vertices)},
            }
        )
        elevation = topography.add_data(
            {"elevation": {"values": topography.vertices[:, 2]}}
        )
    params = MVIInversionOptions.build(
        geoh5=geoh5,
        mesh=mesh,
        data_object=survey,
        tmi_channel=tmi_channel,
        tmi_uncertainty=0.01,
        active_cells=ActiveCellsOptions(
            topography_object=topography, topography=elevation
        ),
        inducing_field_strength=50000.0,
        inducing_field_inclination=60.0,
        inducing_field_declination=0.0,
        starting_model=1.0,
    )

    geoh5 = params.geoh5
    with geoh5.open():
        topo = InversionTopography(geoh5, params)
        locs = topo.get_locations(params.active_cells.topography_object)
        np.testing.assert_allclose(
            locs[:, 2],
            params.active_cells.topography.values,
        )

        # Check that boundary cells are handled properly
        # Shift one of the survey vertices to the corner
        survey.vertices[0, :] = mesh.centroids[0, :]
        geoh5.update_attribute(survey, "vertices")
        inversion_mesh = InversionMesh(geoh5, params)
        inversion_data = InversionData(geoh5, params)
        params.inversion_type = "magnetotellurics"
        active_cells = topo.active_cells(inversion_mesh, inversion_data)

        mesh.add_data(
            {
                "active_cells": {
                    "values": active_cells,
                }
            }
        )
        assert not active_cells[-1]

        # Test flat topo
        params.active_cells.topography = 199.0
        locs = topo.get_locations(params.active_cells.topography_object)
        np.testing.assert_allclose(locs[:, 2], np.ones_like(locs[:, 2]) * 199.0)
