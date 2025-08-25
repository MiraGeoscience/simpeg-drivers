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
from simpeg_drivers.utils.synthetics.driver import SyntheticsComponents
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions as SyntheticsMeshOptions,
)
from simpeg_drivers.utils.synthetics.options import (
    ModelOptions as SyntheticsModelOptions,
)
from simpeg_drivers.utils.synthetics.options import (
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import get_workspace


def test_gravity_plate_simulation(tmp_path):
    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(n_stations=8, n_lines=8, drape=5.0),
        mesh=SyntheticsMeshOptions(),
        model=SyntheticsModelOptions(anomaly=0.0),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)
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
            topography_object=components.topography,
            data_object=components.survey,
            geoh5=geoh5,
            starting_model=0.1,
        )

        gravity_inversion = SimPEGGroup.create(geoh5)
        gravity_inversion.options = options.serialize()

        params = PlateSimulationOptions(
            title="test",
            run_command="run",
            geoh5=geoh5,
            mesh=mesh_params,
            model=model_params,
            simulation=gravity_inversion,
        )
        driver = PlateSimulationDriver(params)
        driver.run()

        assert np.nanmax(driver.model.values) == 0.5
