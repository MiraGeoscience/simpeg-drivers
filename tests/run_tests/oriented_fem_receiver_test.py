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
import pytest
from geoapps_utils.modelling.plates import PlateModel
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup, UIJsonGroup
from geoh5py.objects import AirborneFEMReceivers
from geoh5py.shared.utils import fetch_active_workspace

from simpeg_drivers.electromagnetics.frequency_domain import (
    FDEMForwardDriver,
    FDEMForwardOptions,
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


# To test the full run and validate the inversion.
# Move this file out of the test directory and run.

target_run = {"data_norm": 91.18814842528005, "phi_d": 4250, "phi_m": 968}


def collect_real_components(geoh5):
    # Load results and validate
    data_list = {}
    with fetch_active_workspace(geoh5) as ws:
        group = next(group for group in ws.groups if isinstance(group, UIJsonGroup))
        survey = next(
            child for child in group.children if isinstance(child, AirborneFEMReceivers)
        )
        for comp in "xyz":
            data_group = survey.get_entity(f"Iteration_0_{comp}_real")[0]
            data_list[comp] = np.vstack(
                [survey.get_data(uid)[0].values for uid in data_group.properties]
            )
    return data_list


@pytest.mark.parametrize("azimuth, dip", [(90, 0), (45, 0), (90, 90)])
def test_fem_fwr_run(tmp_path: Path, azimuth, dip):
    """
    Forward simulations with variable receiver orientations.
    The results are not expected to be the same, but should be similar.
    """
    refinement = (2, 4)
    cell_size = (5.0, 5.0, 5.0)
    # Run the forward east-west
    opts = SyntheticsComponentsOptions(
        method="fdem",
        refine_plate=True,
        survey=SurveyOptions(
            height=0.0,
            n_stations=16,
            n_lines=1,
            drape=15.0,
            rotation=90 - azimuth,
            topography=lambda x, y: np.zeros(x.shape),
        ),
        mesh=MeshOptions(
            cell_size=cell_size, refinement=refinement, padding_distance=400.0
        ),
        model=ModelOptions(
            background=1e-3,
            plate=PlateModel(
                strike_length=70.0,
                dip_length=100.0,
                width=10.0,
                origin=(0.0, 0.0, -60.0),
                direction=azimuth,
                dip=45.0,
            ),
        ),
    )

    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        survey = components.survey

        # Create property group with orientation
        dip = np.ones(survey.n_vertices) * dip
        azimuth = np.ones(survey.n_vertices) * azimuth
        data_list = survey.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            survey, properties=data_list, property_group_type="Dip direction & dip"
        )

        params = FDEMForwardOptions.build(
            geoh5=geoh5,
            title=f"Forward: Azimuth {azimuth}, Dip {dip}",
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            z_real_channel_bool=True,
            z_imag_channel_bool=True,
            x_real_channel_bool=True,
            x_imag_channel_bool=True,
            y_real_channel_bool=True,
            y_imag_channel_bool=True,
            receivers_orientation=pg,
        )

    fwr_driver = FDEMForwardDriver(params)
    fwr_driver.run()


def test_validate_orientations(tmp_path: Path):

    with Workspace(
        tmp_path / "../test_fem_fwr_run_90_0_0/inversion_test.ui.geoh5"
    ) as geoh5:
        sim_90_0 = collect_real_components(geoh5)

    with Workspace(
        tmp_path / "../test_fem_fwr_run_45_0_0/inversion_test.ui.geoh5"
    ) as geoh5:
        sim_45_0 = collect_real_components(geoh5)

    # Components almost the same at 45
    assert np.mean((sim_90_0["y"] - sim_45_0["y"]) / sim_90_0["y"]) < 0.2

    with Workspace(
        tmp_path / "../test_fem_fwr_run_90_90_0/inversion_test.ui.geoh5"
    ) as geoh5:
        sim_90_90 = collect_real_components(geoh5)

    # 90 dip makes Y point down and Z east, so Y should be -Z, and Z should be Y
    assert np.mean((sim_90_0["y"] - sim_90_90["z"]) / sim_90_0["y"]) < 0.2
    assert np.mean((sim_90_0["z"] + sim_90_90["y"]) / sim_90_0["z"]) < 0.2
