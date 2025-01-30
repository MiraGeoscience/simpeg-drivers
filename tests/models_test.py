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
from geoh5py.objects import Points

from simpeg_drivers.components import (
    InversionMesh,
    InversionModel,
    InversionModelCollection,
)
from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.potential_fields import MagneticVectorInversionParams
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MagneticVectorInversionDriver,
)
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def get_mvi_params(tmp_path: Path) -> MagneticVectorInversionParams:
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
    tmi_channel = survey.add_data(
        {
            "tmi": {"values": np.random.rand(survey.n_vertices)},
        }
    )
    elevation = topography.add_data(
        {"elevation": {"values": topography.vertices[:, 2]}}
    )
    params = MagneticVectorInversionParams(
        geoh5=geoh5,
        data_object=survey,
        tmi_channel=tmi_channel,
        mesh=mesh,
        active_cells=ActiveCellsData(
            topography_object=topography, topography=elevation
        ),
        starting_model=1e-04,
        inducing_field_inclination=79.0,
        inducing_field_declination=11.0,
        reference_model=0.0,
        reference_inclination=79.0,
        reference_declination=11.0,
    )

    return params


def test_zero_reference_model(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    driver = MagneticVectorInversionDriver(params)
    _ = InversionModel(driver, "reference")
    incl = np.unique(geoh5.get_entity("reference_inclination")[0].values)
    decl = np.unique(geoh5.get_entity("reference_declination")[0].values)
    assert len(incl) == 1
    assert len(decl) == 1
    assert np.isclose(incl[0], 79.0)
    assert np.isclose(decl[0], 11.0)


def test_collection(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    driver = MagneticVectorInversionDriver(params)
    models = InversionModelCollection(driver)
    models.remove_air(driver.models.active_cells)
    starting = InversionModel(driver, "starting")
    starting.remove_air(driver.models.active_cells)
    np.testing.assert_allclose(models.starting, starting.model, atol=1e-7)


def test_initialize(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    driver = MagneticVectorInversionDriver(params)
    starting_model = InversionModel(driver, "starting")
    assert len(starting_model.model) == 3 * driver.inversion_mesh.n_cells
    assert len(np.unique(starting_model.model)) == 3


def test_model_from_object(tmp_path: Path):
    # Test behaviour when loading model from Points object with non-matching mesh
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    driver = MagneticVectorInversionDriver(params)

    inversion_mesh = InversionMesh(geoh5, params)
    cc = inversion_mesh.mesh.cell_centers
    m0 = np.array([2.0, 3.0, 1.0])
    vals = (m0[0] * cc[:, 0]) + (m0[1] * cc[:, 1]) + (m0[2] * cc[:, 2])

    point_object = Points.create(geoh5, name="test_point", vertices=cc)
    point_object.add_data({"test_data": {"values": vals}})
    data_object = geoh5.get_entity("test_data")[0]
    params.lower_bound = data_object
    lower_bound = InversionModel(driver, "lower_bound")
    nc = int(len(lower_bound.model) / 3)
    A = driver.inversion_mesh.mesh.cell_centers
    b = lower_bound.model[:nc]
    from scipy.linalg import lstsq

    m = lstsq(A, b)[0]
    np.testing.assert_array_almost_equal(m, m0, decimal=1)
