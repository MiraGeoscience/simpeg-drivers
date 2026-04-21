# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import AirborneTEMReceivers, MaxwellPlate, Octree

from simpeg_drivers.electromagnetics.time_domain import (
    TDEMForwardOptions,
)
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
from tests.utils.runtests import run_driver_from_ui_json
from tests.utils.targets import get_workspace


def test_leroi_run(tmp_path):

    with Workspace(tmp_path / "leroi_test.geoh5") as geoh5:
        geometry = PlateModel(
            easting=0.0,
            northing=0.0,
            elevation=100.0,
            width=10.0,
            strike_length=200.0,
            dip_length=100.0,
            dip=80.0,
            direction=90.0,
        )

        opts = SyntheticsComponentsOptions(
            method="airborne tdem",
            survey=SurveyOptions(width=800.0, n_stations=32, n_lines=4, drape=40.0),
            mesh=SyntheticsMeshOptions(),
            model=SyntheticsModelOptions(
                anomaly=1 / 10,
                background=1 / 5000,
                plate=geometry,
            ),
        )
        components = SyntheticsComponents(geoh5, options=opts)
        out_group = SimPEGGroup.create(geoh5, name="TEM forward")
        options = TDEMForwardOptions.build(
            topography_object=components.topography,
            data_object=components.survey,
            geoh5=geoh5,
            starting_model=components.model,
            z_channel_bool=True,
            out_group=out_group,
        )
        options.update_out_group_options()

        params = PlateSimulationOptions(
            geoh5=geoh5,
            mesh=MeshOptions(
                u_cell_size=25.0,
                v_cell_size=25.0,
                w_cell_size=25.0,
                padding_distance=1000.0,
                depth_core=600.0,
                max_distance=200.0,
                survey_refinement=[2, 4],
                topography_refinement=[0, 1],
                plate_refinement=[2, 2],
            ),
            model=ModelOptions(
                background=2000.0,
                overburden_options=OverburdenOptions(
                    thickness=50.0,
                    overburden_property=1500.0,
                ),
                plate_options=PlateOptions(
                    name="plate",
                    geometry=geometry,
                    plate_property=1.0,
                ),
            ),
            simulation=options.out_group,
            use_leroi=True,
        )

    run_driver_from_ui_json(params)

    with Workspace(tmp_path / "leroi_test.geoh5") as geoh5:
        plate_simulation_group = geoh5.get_entity("Plate Simulation")[0]
        forward_group = geoh5.get_entity("TEM forward")[0]
        assert forward_group.parent == plate_simulation_group

        survey = forward_group.get_entity("survey")[0]
        assert isinstance(survey, AirborneTEMReceivers)

        maxwell_plate = plate_simulation_group.get_entity("Maxwell Plate")[0]
        assert isinstance(maxwell_plate, MaxwellPlate)

        expected_channels = [
            "fwd inline [0]",
            "fwd inline [1]",
            "fwd inline [2]",
            "fwd crossline [0]",
            "fwd crossline [1]",
            "fwd crossline [2]",
            "fwd vertical [0]",
            "fwd vertical [1]",
            "fwd vertical [2]",
        ]
        for channel in expected_channels:
            assert survey.get_entity(channel)[0] is not None
