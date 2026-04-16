# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import subprocess

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups import SimPEGGroup

from simpeg_drivers.electromagnetics.time_domain import (
    TDEMForwardOptions,
)
from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.models.options import (
    ModelOptions,
    OverburdenOptions,
    PlateOptions,
)
from simpeg_drivers.plate_simulation.options import MeshOptions, PlateSimulationOptions
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


def test_leroi_executable(tmp_path):
    control_file = tmp_path / "test.cfl"
    control_file.touch()
    subprocess.run("F2.bat test output", cwd=tmp_path, shell=True, check=False)


def test_leroi_run(tmp_path):
    opts = SyntheticsComponentsOptions(
        method="airborne tdem",
        survey=SurveyOptions(n_stations=8, n_lines=8, drape=40.0),
        mesh=SyntheticsMeshOptions(),
        model=SyntheticsModelOptions(background=1.0 / 2000.0),
    )
    with get_workspace(tmp_path / "leroi_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        mesh_params = MeshOptions(
            u_cell_size=25.0,
            v_cell_size=25.0,
            w_cell_size=25.0,
            padding_distance=1000.0,
            depth_core=600.0,
            max_distance=200.0,
            survey_refinement=[2, 4],
            topography_refinement=[0, 1],
            plate_refinement=[2, 2],
        )

        overburden_params = OverburdenOptions(
            thickness=50.0,
            overburden_property=1500.0,  # overburden resistivity (ohm-m)
        )

        plate_params = PlateOptions(
            name="plate",
            geometry=PlateModel(
                easting=0.0,
                northing=0.0,
                elevation=-50.0,
                width=10.0,
                strike_length=200.0,
                dip_length=100.0,
                dip=80.0,
                direction=90.0,
            ),
            plate_property=1.0,  # plate resistivity (ohm-m)
        )

        model_params = ModelOptions(
            background=2000.0,  # background resistivity (ohm-m)
            overburden_options=overburden_params,
            plate_options=plate_params,
        )

        options = TDEMForwardOptions.build(
            topography_object=components.topography,
            data_object=components.survey,
            geoh5=geoh5,
            starting_model=1.0 / 2000.0,  # background conductivity (S/m)
            z_channel_bool=True,
        )

        tdem_group = SimPEGGroup.create(geoh5)
        tdem_group.options = options.serialize()

        params = PlateSimulationOptions(
            title="test_leroi",
            run_command="run",
            geoh5=geoh5,
            mesh=mesh_params,
            model=model_params,
            simulation=tdem_group,
            use_leroi=True,
        )

        driver = PlateSimulationDriver(params)
        driver.run()
