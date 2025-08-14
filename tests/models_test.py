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
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields import MVIInversionOptions
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MVIInversionDriver,
)
from simpeg_drivers.utils.synthetics.driver import setup_inversion_workspace
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)


def get_mvi_params(tmp_path: Path) -> MVIInversionOptions:
    opts = SyntheticsComponentsOptions(
        survey=SurveyOptions(n_stations=2, n_lines=2),
        mesh=MeshOptions(refinement=(2,)),
        model=ModelOptions(anomaly=0.05),
    )

    geoh5, entity, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="magnetic_vector", options=opts
    )
    with geoh5.open():
        mesh = model.parent
        ref_inducing = mesh.add_data(
            {
                "reference_inclination": {"values": np.ones(mesh.n_cells) * 79.0},
                "reference_declination": {"values": np.ones(mesh.n_cells) * 11.0},
            }
        )
        tmi_channel = survey.add_data(
            {
                "tmi": {"values": np.random.rand(survey.n_vertices)},
            }
        )
        elevation = topography.add_data(
            {"elevation": {"values": topography.vertices[:, 2]}}
        )
    params = MVIInversionOptions.build(
        geoh5=geoh5,
        data_object=survey,
        tmi_channel=tmi_channel,
        tmi_uncertainty=1.0,
        mesh=mesh,
        active_cells=ActiveCellsOptions(
            topography_object=topography, topography=elevation
        ),
        starting_model=1e-04,
        inducing_field_inclination=79.0,
        inducing_field_declination=11.0,
        reference_model=0.0,
        inducing_field_strength=50000.0,
        reference_inclination=ref_inducing[0],
        reference_declination=ref_inducing[1],
    )

    return params


def test_zero_reference_model(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    with geoh5.open():
        driver = MVIInversionDriver(params)
        _ = InversionModel(driver, "reference_model")
        incl = np.unique(geoh5.get_entity("reference_inclination")[0].values)
        decl = np.unique(geoh5.get_entity("reference_declination")[0].values)
    assert len(incl) == 1
    assert len(decl) == 1
    assert np.isclose(incl[0], 79.0)
    assert np.isclose(decl[0], 11.0)


def test_collection(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    with params.geoh5.open():
        driver = MVIInversionDriver(params)
        models = InversionModelCollection(driver)
        models.remove_air(driver.models.active_cells)
        starting = InversionModel(driver, "starting_model")
        starting.remove_air(driver.models.active_cells)
        assert len(models.starting_model) == 3 * len(starting.model)
        np.testing.assert_allclose(
            np.linalg.norm(models.starting_model.reshape((-1, 3), order="F"), axis=1),
            starting.model,
            atol=1e-7,
        )


def test_initialize(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    with params.geoh5.open():
        driver = MVIInversionDriver(params)
        starting_model = InversionModel(driver, "starting_model")
        assert len(starting_model.model) == driver.inversion_mesh.n_cells
        assert len(np.unique(starting_model.model)) == 1


def test_model_from_object(tmp_path: Path):
    # Test behaviour when loading model from Points object with non-matching mesh
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    with geoh5.open():
        driver = MVIInversionDriver(params)

        inversion_mesh = InversionMesh(geoh5, params)
        cc = inversion_mesh.mesh.cell_centers
        m0 = np.array([2.0, 3.0, 1.0])
        vals = (m0[0] * cc[:, 0]) + (m0[1] * cc[:, 1]) + (m0[2] * cc[:, 2])

        point_object = Points.create(geoh5, name="test_point", vertices=cc)
        point_object.add_data({"test_data": {"values": vals}})
        data_object = geoh5.get_entity("test_data")[0]
        params.models.upper_bound = data_object
        upper_bound = InversionModel(driver, "upper_bound")

        A = driver.inversion_mesh.mesh.cell_centers
        b = upper_bound.model
        from scipy.linalg import lstsq

        m = lstsq(A, b)[0]
        np.testing.assert_array_almost_equal(m, m0, decimal=1)
