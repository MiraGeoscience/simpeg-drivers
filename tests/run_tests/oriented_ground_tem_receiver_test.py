# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=too-many-locals

from __future__ import annotations

from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.transformations import (
    cartesian_to_spherical,
    x_rotation_matrix,
    z_rotation_matrix,
)
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup
from geoh5py.objects import LargeLoopGroundTEMReceivers

from simpeg_drivers.electromagnetics.time_domain.forward import (
    TDEMForwardDriver,
    TDEMForwardOptions,
)
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import get_workspace


def test_tem_fwr_run(tmp_path: Path):
    """
    Forward simulations with variable receiver orientations.
    The results are not expected to be the same, but should be similar.
    """
    refinement = (2, 4)
    cell_size = (5.0, 5.0, 5.0)
    # Run the forward east-west
    opts = SyntheticsComponentsOptions(
        method="ground tdem",
        refine_plate=True,
        survey=SurveyOptions(
            n_stations=4,
            n_lines=4,
            drape=5.0,
            rotation=90,
            topography=lambda x, y: np.zeros(x.shape),
        ),
        mesh=MeshOptions(
            u_cell_size=cell_size[0],
            v_cell_size=cell_size[1],
            w_cell_size=cell_size[2],
            survey_refinement=list(refinement),
            topography_refinement=[0, 0, 1],
            plate_refinement=[1],
            padding_distance=400.0,
        ),
        model=ModelOptions(
            background=1e-3,
            plate=PlateModel(
                strike_length=150.0,
                dip_length=100.0,
                width=10.0,
                easting=0.0,
                northing=0.0,
                elevation=-60.0,
            ),
        ),
    )

    with get_workspace(tmp_path / f"{__name__}.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        survey = components.survey

        # Create property group with orientation
        params = TDEMForwardOptions.build(
            geoh5=geoh5,
            title="Normal",
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            z_channel_bool=True,
            x_channel_bool=True,
            y_channel_bool=True,
        )

    fwr_driver = TDEMForwardDriver(params)
    fwr_driver.run()
    with survey.workspace.open() as ws:
        norm_sim = ws.get_entity("Normal")[0]
        norm_survey = next(
            child
            for child in norm_sim.children
            if isinstance(child, LargeLoopGroundTEMReceivers)
        )
        norm_vals = []

        for comp in ["crossline", "inline", "vertical"]:
            norm_vals.append(
                norm_survey.get_entity(f"Iteration_0_{comp}_[0]")[0].values
            )

        norm_vals = np.vstack(norm_vals)
        norm_vals /= np.linalg.norm(norm_vals, axis=0)[np.newaxis, :]

        rad_azm_dip = cartesian_to_spherical(norm_vals.T)
        azimuth = 90 - np.rad2deg(rad_azm_dip[:, 1])
        dip = -(90 - np.rad2deg(rad_azm_dip[:, 2]))
        data_list = survey.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            survey, properties=data_list, property_group_type="Dip direction & dip"
        )
        data_list = norm_survey.add_data(
            {
                "hx": {"values": norm_vals[0, :]},
                "hy": {"values": norm_vals[1, :]},
                "hz": {"values": norm_vals[2, :]},
            }
        )
        PropertyGroup(
            norm_survey,
            properties=data_list,
            property_group_type="3D vector",
            name="fields",
        )

    # Repeat with rotation
    params.receivers_orientation = pg
    params.out_group = None
    params.title = "Rotated"
    fwr_driver_rot = TDEMForwardDriver(params)
    fwr_driver_rot.run()

    with Workspace(tmp_path / f"{__name__}.geoh5", mode="r+") as ws:
        rot_sim = ws.get_entity("Rotated")[0]
        rot_survey = next(
            child
            for child in rot_sim.children
            if isinstance(child, LargeLoopGroundTEMReceivers)
        )

        rot_vals = []

        for comp in ["crossline", "inline", "vertical"]:
            rot_vals.append(rot_survey.get_entity(f"Iteration_0_{comp}_[0]")[0].values)

        rot_vals = np.vstack(rot_vals)
        rot_vals /= np.linalg.norm(rot_vals, axis=0)[np.newaxis, :]

        # Check that the total fields are preserved
        np.testing.assert_allclose(
            np.linalg.norm(rot_vals, axis=0), np.linalg.norm(norm_vals, axis=0)
        )

        # Rotate back and validate components
        rot_x = x_rotation_matrix(np.deg2rad(-dip))
        rot_z = z_rotation_matrix(np.deg2rad(-azimuth))
        back_vals = (rot_z @ (rot_x @ rot_vals.T.flatten())).reshape((3, -1), order="F")

        np.testing.assert_allclose(back_vals, np.vstack(norm_vals))
