# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup

from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.models.options import (
    ModelOptions,
    OverburdenOptions,
    PlateOptions,
)
from simpeg_drivers.plate_simulation.options import MeshOptions, PlateSimulationOptions
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from tests.testing_utils import setup_inversion_workspace


def test_gravity_plate_simulation(tmp_path):
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path,
        background=0.0,
        anomaly=0.0,
        n_electrodes=8,
        n_lines=8,
        inversion_type="gravity",
        flatten=False,
    )

    with geoh5.open() as ws:
        mesh_params = MeshOptions(
            u_cell_size=10.0,
            v_cell_size=10.0,
            w_cell_size=10.0,
            padding_distance=1500.0,
            depth_core=600.0,
            max_distance=200.0,
        )

        overburden_params = OverburdenOptions(thickness=50.0, overburden=0.2)

        plate_params = PlateOptions(
            name="plate",
            plate=0.5,
            elevation=-250.0,
            width=100.0,
            strike_length=100.0,
            dip_length=100.0,
            dip=0.0,
            dip_direction=0.0,
            reference="center",
        )

        model_params = ModelOptions(
            name="density",
            background=0.0,
            overburden_model=overburden_params,
            plate_model=plate_params,
        )

        options = GravityForwardOptions.build(
            topography_object=topography,
            data_object=survey,
            geoh5=ws,
            starting_model=0.1,
        )

        gravity_inversion = SimPEGGroup.create(ws)
        gravity_inversion.options = options.serialize()

        params = PlateSimulationOptions(
            title="test",
            run_command="run",
            geoh5=ws,
            mesh=mesh_params,
            model=model_params,
            simulation=gravity_inversion,
        )
        driver = PlateSimulationDriver(params)
        driver.run()

        assert np.nanmax(driver.model.values) == 0.5
