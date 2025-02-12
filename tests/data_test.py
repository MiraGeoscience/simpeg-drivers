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
import pytest
import simpeg
from discretize.utils import mesh_builder_xyz
from geoh5py.objects import Points
from geoh5py.workspace import Workspace
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.utils import treemesh_2_octree

from simpeg_drivers.components import InversionData
from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.potential_fields.magnetic_vector.driver import (
    MagneticVectorInversionDriver,
)
from simpeg_drivers.potential_fields.magnetic_vector.params import (
    MagneticVectorInversionParams,
)
from simpeg_drivers.utils.testing import Geoh5Tester, setup_inversion_workspace


def get_mvi_params(tmp_path: Path, **kwargs) -> MagneticVectorInversionParams:
    geoh5, entity, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.05,
        refinement=(2,),
        n_electrodes=2,
        n_lines=2,
        inversion_type="magnetic_vector",
    )
    tmi_channel = survey.add_data(
        {"tmi": {"values": np.random.rand(survey.n_vertices)}}
    )
    params = MagneticVectorInversionParams(
        geoh5=geoh5,
        data_object=survey,
        tmi_channel=tmi_channel,
        active_cells=ActiveCellsData(topography_object=topography),
        mesh=model.parent,
        starting_model=model,
        **kwargs,
    )
    return params


def test_save_data(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    data = InversionData(geoh5, params)

    assert len(data.entity.vertices) > 0


def test_survey_data(tmp_path: Path):
    X, Y, Z = np.meshgrid(np.linspace(0, 100, 3), np.linspace(0, 100, 3), 0)
    verts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    with Workspace(tmp_path / "test_workspace.geoh5") as workspace:
        test_data_object = Points.create(
            workspace, vertices=verts, name="test_data_object"
        )
        bxx_data, byy_data, bzz_data = test_data_object.add_data(
            {
                "bxx": {
                    "association": "VERTEX",
                    "values": np.arange(len(verts)).astype(float),
                },
                "byy": {
                    "association": "VERTEX",
                    "values": len(verts) + np.arange(len(verts)).astype(float),
                },
                "bzz": {
                    "association": "VERTEX",
                    "values": 2 * len(verts) + np.arange(len(verts)).astype(float),
                },
            }
        )
        test_topo_object = Points.create(
            workspace, vertices=verts, name="test_topo_object"
        )
        _ = test_topo_object.add_data(
            {"elev": {"association": "VERTEX", "values": 100 * np.ones(len(verts))}}
        )
        topo = workspace.get_entity("elev")[0]
        mesh = mesh_builder_xyz(
            verts,
            [20, 20, 20],
            depth_core=50,
            mesh_type="TREE",
        )
        mesh = OctreeDriver.refine_tree_from_surface(
            mesh,
            test_topo_object,
            levels=[2],
            diagonal_balance=False,
            finalize=True,
        )

        mesh = treemesh_2_octree(workspace, mesh)
        active_cells = ActiveCellsData(
            topography_object=test_topo_object, topography=topo
        )
        params = MagneticVectorInversionParams(
            geoh5=workspace,
            data_object=test_data_object,
            active_cells=active_cells,
            bxx_channel=bxx_data,
            bxx_uncertainty=0.1,
            byy_channel=byy_data,
            byy_uncertainty=0.2,
            bzz_channel=bzz_data,
            bzz_uncertainty=0.3,
            mesh=mesh,
            starting_model=0.0,
            tile_spatial=2,
            z_from_topo=True,
            resolution=0.0,
        )

        driver = MagneticVectorInversionDriver(params)

    assert driver.inversion is not None

    local_survey_a = (
        driver.inverse_problem.dmisfit.objfcts[0].simulation.simulations[0].survey
    )
    local_survey_b = (
        driver.inverse_problem.dmisfit.objfcts[1].simulation.simulations[0].survey
    )

    # test locations

    np.testing.assert_array_equal(
        verts[driver.sorting[0], :2], local_survey_a.receiver_locations[:, :2]
    )
    np.testing.assert_array_equal(
        verts[driver.sorting[1], :2], local_survey_b.receiver_locations[:, :2]
    )
    assert all(local_survey_a.receiver_locations[:, 2] == 100.0)
    assert all(local_survey_b.receiver_locations[:, 2] == 100.0)

    # test observed data
    sorting = np.hstack(driver.sorting)
    expected_dobs = np.column_stack(
        [bxx_data.values, byy_data.values, bzz_data.values]
    )[sorting].ravel()
    survey_dobs = [local_survey_a.dobs, local_survey_b.dobs]
    np.testing.assert_array_equal(expected_dobs, np.hstack(survey_dobs))

    # test save geoh5 iteration data
    driver.directives.save_iteration_data_directive.write(99, survey_dobs)

    with workspace.open():
        bxx_test = workspace.get_entity("Iteration_99_bxx")[0].values
        byy_test = workspace.get_entity("Iteration_99_byy")[0].values
        bzz_test = workspace.get_entity("Iteration_99_bzz")[0].values

    np.testing.assert_array_equal(bxx_test, bxx_data.values)
    np.testing.assert_array_equal(byy_test, byy_data.values)
    np.testing.assert_array_equal(bzz_test, bzz_data.values)

    driver.directives.save_iteration_residual_directive.write(99, survey_dobs)

    with workspace.open():
        assert np.all(
            workspace.get_entity("Iteration_99_bxx_Residual")[0].values == 0
        ), "Residual data should be zero."
        assert np.all(
            workspace.get_entity("Iteration_99_byy_Residual")[0].values == 0
        ), "Residual data should be zero."
        assert np.all(
            workspace.get_entity("Iteration_99_bzz_Residual")[0].values == 0
        ), "Residual data should be zero."


def test_has_tensor():
    assert InversionData.check_tensor(["Gxx"])
    assert InversionData.check_tensor(["Gxy"])
    assert InversionData.check_tensor(["Gxz"])
    assert InversionData.check_tensor(["Gyy"])
    assert InversionData.check_tensor(["Gyx"])
    assert InversionData.check_tensor(["Gyz"])
    assert InversionData.check_tensor(["Gzz"])
    assert InversionData.check_tensor(["Gzx"])
    assert InversionData.check_tensor(["Gzy"])
    assert InversionData.check_tensor(["Gxx", "Gyy", "tmi"])
    assert not InversionData.check_tensor(["tmi"])


def test_get_uncertainty_component(tmp_path: Path):
    params = get_mvi_params(tmp_path, tmi_uncertainty=1.0)
    geoh5 = params.geoh5
    data = InversionData(geoh5, params)
    unc = params.uncertainties["tmi"]
    assert len(np.unique(unc)) == 1
    assert np.unique(unc)[0] == 1
    assert len(unc) == data.entity.n_vertices


def test_normalize(tmp_path: Path):
    params = get_mvi_params(tmp_path)
    geoh5 = params.geoh5
    data = InversionData(geoh5, params)
    data.normalizations = data.get_normalizations()
    test_data = data.normalize(data.observed)
    assert all(test_data["tmi"] == params.data["tmi"])
    assert len(test_data) == 1


def test_get_survey(tmp_path: Path):
    params = get_mvi_params(tmp_path, tmi_uncertainty=1.0)
    geoh5 = params.geoh5
    data = InversionData(geoh5, params)
    survey = data.create_survey()
    assert isinstance(survey[0], simpeg.potential_fields.magnetics.Survey)
