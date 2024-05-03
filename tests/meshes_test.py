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
from geoh5py.groups import SimPEGGroup

from simpeg_drivers.components import InversionData, InversionMesh, InversionTopography
from simpeg_drivers.potential_fields import MagneticVectorParams
from simpeg_drivers.potential_fields.magnetic_vector.driver import MagneticVectorDriver
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

    ws, params = setup_params(tmp_path)

    validation_mesh = params.mesh.copy(copy_children=True)
    validation_mesh.name = "validation"
    validation_params = MagneticVectorParams(
        geoh5=ws,
        mesh=validation_mesh,
        starting_model=validation_mesh.get_data("model")[0],
        data_object=params.data_object.copy(copy_children=False),
        topography_object=params.topography_object.copy(),
        tmi_channel_bool=True,
        forward_only=True,
        out_group=SimPEGGroup.create(ws, name="validation_group"),
    )
    driver = MagneticVectorDriver(validation_params)
    driver.run()

    test_mesh = params.mesh.copy(copy_children=True)
    test_mesh.name = "test"
    test_mesh.origin["z"] += test_mesh.w_count * test_mesh.w_cell_size
    test_mesh.w_cell_size *= -1
    test_params = MagneticVectorParams(
        geoh5=ws,
        mesh=test_mesh,
        starting_model=test_mesh.get_data("model")[0],
        data_object=params.data_object.copy(copy_children=False),
        topography_object=params.topography_object.copy(),
        tmi_channel_bool=True,
        forward_only=True,
        out_group=SimPEGGroup.create(ws, name="test_group"),
    )
    driver = MagneticVectorDriver(test_params)
    driver.run()
    ws.close()

    with ws.open():

        data = ws.get_entity("Iteration_0_tmi")
        test_data = data[0].values
        validation_data = data[1].values
        active = ws.get_entity("active_cells")
        test_active = active[0].values
        validation_active = active[1].values

        test_mesh = InversionMesh.ensure_cell_convention(test_mesh)
        assert test_mesh.w_cell_size == 5.0
        assert test_mesh.origin["z"] == validation_mesh.origin["z"]
        assert np.allclose(test_mesh.centroids, validation_mesh.centroids)
        assert np.allclose(test_data, validation_data)
        assert np.allclose(test_active, validation_active)


def test_raise_on_rotated_negative_cell_size(tmp_path):
    ws, params = setup_params(tmp_path)
    mesh = params.mesh
    mesh.rotation = 20.0
    mesh.w_cell_size *= -1
    msg = "Cannot convert negative cell sizes for rotated mesh."
    with pytest.raises(ValueError, match=msg):
        InversionMesh.ensure_cell_convention(mesh)
    ws.close()


def test_negative_cell_size_inversion(tmp_path):

    ws, params = setup_params(tmp_path)

    validation_mesh = params.mesh.copy(copy_children=True)
    validation_mesh.name = "validation"
    inducing_field = (50000.0, 90.0, 0.0)
    validation_params = MagneticVectorParams(
        geoh5=ws,
        mesh=validation_mesh,
        starting_model=validation_mesh.get_data("model")[0],
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        data_object=params.data_object.copy(copy_children=False),
        topography_object=params.topography_object.copy(),
        tmi_channel_bool=True,
        forward_only=True,
        out_group=SimPEGGroup.create(ws, name="validation_group"),
    )
    driver = MagneticVectorDriver(validation_params)
    driver.run()
    ws.close()

    with ws.open():
        data_object = ws.get_entity("survey")[0]
        data = ws.get_entity("Iteration_0_tmi")[0].copy()
        data.name = "tmi_data"

        test_mesh = params.mesh.copy(copy_children=True)
        test_mesh.name = "test"
        test_mesh.origin["z"] += test_mesh.w_count * test_mesh.w_cell_size
        test_mesh.w_cell_size *= -1

        test_params = MagneticVectorParams(
            geoh5=ws,
            mesh=test_mesh,
            starting_model=1e-4,
            reference_model=0.0,
            inducing_field_strength=inducing_field[0],
            inducing_field_inclination=inducing_field[1],
            inducing_field_declination=inducing_field[2],
            data_object=data_object,
            tmi_channel=data,
            tmi_uncertainty=4.0,
            topography_object=params.topography_object.copy(),
            out_group=SimPEGGroup.create(ws, name="test_group"),
            s_norm=0.0,
            x_norm=1.0,
            y_norm=1.0,
            z_norm=1.0,
            gradient_type="components",
            initial_beta_ratio=1e1,
            prctile=100,
            store_sensitivities="ram",
            max_global_iterations=2,
        )
        driver = MagneticVectorDriver(test_params)
        driver.run()
