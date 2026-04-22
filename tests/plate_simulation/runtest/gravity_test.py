# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.groups import SimPEGGroup

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
from tests.utils.runtests import run_driver_from_ui_json
from tests.utils.targets import get_workspace


def test_gravity_plate_simulation(tmp_path):

    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        geometry = PlateModel(
            elevation=100.0,
            width=100.0,
            strike_length=100.0,
            dip_length=100.0,
            dip=0.0,
            direction=0.0,
        )

        opts = SyntheticsComponentsOptions(
            method="gravity",
            survey=SurveyOptions(n_stations=8, n_lines=8, drape=5.0),
            mesh=SyntheticsMeshOptions(),
            model=SyntheticsModelOptions(anomaly=0.0),
        )

        components = SyntheticsComponents(geoh5, options=opts)
        out_group = SimPEGGroup.create(geoh5, name="Gravity forward")
        options = GravityForwardOptions.build(
            topography_object=components.topography,
            data_object=components.survey,
            geoh5=geoh5,
            starting_model=0.1,
            out_group=out_group,
        )
        options.update_out_group_options()

        params = PlateSimulationOptions(
            geoh5=geoh5,
            mesh=MeshOptions(
                u_cell_size=10.0,
                v_cell_size=10.0,
                w_cell_size=10.0,
                padding_distance=1500.0,
                depth_core=600.0,
                max_distance=200.0,
                survey_refinement=[4, 6],
                topography_refinement=[0, 1],
                plate_refinement=[4, 2],
            ),
            model=ModelOptions(
                name="density",
                background=0.0,
                overburden_options=OverburdenOptions(
                    thickness=50.0, overburden_property=0.2
                ),
                plate_options=PlateOptions(
                    name="plate",
                    geometry=geometry,
                    plate_property=0.5,
                ),
            ),
            simulation=options.out_group,
        )

        driver = run_driver_from_ui_json(params)

        assert (
            np.nanmax(driver.simulation_parameters.models.starting_model.values) == 0.5
        )
