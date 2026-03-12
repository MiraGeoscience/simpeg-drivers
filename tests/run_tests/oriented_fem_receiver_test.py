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
from geoh5py.groups import PropertyGroup

from simpeg_drivers.electromagnetics.frequency_domain.driver import (
    FDEMForwardDriver,
)
from simpeg_drivers.electromagnetics.frequency_domain.options import (
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


def test_fem_fwr_run(
    tmp_path: Path,
    refinement=(4,),
    cell_size=(10.0, 10.0, 10.0),
):
    # Run the forward east-west
    opts = SyntheticsComponentsOptions(
        method="fdem",
        survey=SurveyOptions(
            height=0.0,
            n_stations=16,
            n_lines=1,
            drape=15.0,
            rotation=0,
            topography=lambda x, y: np.zeros(x.shape),
            name="survey - EW",
        ),
        mesh=MeshOptions(
            cell_size=cell_size, refinement=refinement, padding_distance=400.0
        ),
        model=ModelOptions(
            background=1e-3,
            plate=PlateModel(
                strike_length=100.0,
                dip_length=100.0,
                width=20.0,
                origin=(0.0, 0.0, -40.0),
                direction=90.0,
                dip=45.0,
            ),
        ),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
        params = FDEMForwardOptions.build(
            geoh5=geoh5,
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
        )

    fwr_driver = FDEMForwardDriver(params)
    fwr_driver.run()

    # Repeat at 45 azimuth
    opts = SyntheticsComponentsOptions(
        method="fdem",
        survey=SurveyOptions(
            height=0.0,
            n_stations=16,
            n_lines=1,
            drape=15.0,
            rotation=45,
            topography=lambda x, y: np.zeros(x.shape),
            name="survey - ROT 45",
        ),
        mesh=MeshOptions(
            cell_size=cell_size,
            refinement=refinement,
            padding_distance=400.0,
            name="mesh - ROT 45",
        ),
        model=ModelOptions(
            background=1e-3,
            plate=PlateModel(
                strike_length=100.0,
                dip_length=100.0,
                width=20.0,
                origin=(0.0, 0.0, -40.0),
                direction=45.0,
                dip=45.0,
            ),
            name="model - ROT 45",
        ),
    )
    with geoh5.open():
        components = SyntheticsComponents(geoh5, options=opts)
        mesh = components.mesh
        # Create property group with orientation
        dip = np.ones(mesh.n_cells) * 0
        azimuth = np.ones(mesh.n_cells) * 45
        data_list = mesh.add_data(
            {
                "azimuth": {"values": azimuth},
                "dip": {"values": dip},
            }
        )
        pg = PropertyGroup(
            mesh, properties=data_list, property_group_type="Dip direction & dip"
        )

        params = FDEMForwardOptions.build(
            geoh5=geoh5,
            mesh=components.mesh,
            topography_object=components.topography,
            data_object=components.survey,
            starting_model=components.model,
            title="FDEM Forward Run 45",
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
