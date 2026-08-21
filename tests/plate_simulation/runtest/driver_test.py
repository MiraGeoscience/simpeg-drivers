# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import logging

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import UIJson

from simpeg_drivers import assets_path
from simpeg_drivers.plate_simulation.driver import (
    PlateSimulationOptions,
)
from simpeg_drivers.plate_simulation.models.options import ModelOptions
from simpeg_drivers.plate_simulation.options import MeshOptions
from simpeg_drivers.potential_fields.gravity.forward import GravityForwardDriver
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


# pylint: disable=too-many-statements
def test_plate_simulation_params_from_input_file(tmp_path, caplog):
    opts = SyntheticsComponentsOptions(
        method="gravity",
        survey=SurveyOptions(n_stations=8, n_lines=8),
        mesh=SyntheticsMeshOptions(),
        model=SyntheticsModelOptions(anomaly=0.0),
    )
    with get_workspace(tmp_path / "inversion_test.ui.geoh5") as geoh5:
        components = SyntheticsComponents(geoh5, options=opts)

        # Add simulation parameter
        options = GravityForwardOptions.model_construct()
        fwr_ifile = UIJson.read(options.default_ui_json)
        options_dict = {
            "inversion_type": "gravity",
            "forward_only": True,
            "topography_object": str(components.topography.uid),
            "data_object": str(components.survey.uid),
            "title": "gravity fwd",
        }
        fwr_ifile.set_values(**options_dict)
        options_dict = fwr_ifile.to_params(workspace=geoh5)
        options = GravityForwardOptions.build(options_dict)
        driver = GravityForwardDriver(options)
        gravity_inversion = driver.validate_out_group(options.out_group)

        ifile = UIJson.read(assets_path() / "uijson" / "plate_simulation.ui.json")
        options_dict = {
            "simulation": gravity_inversion,
            # Add mesh parameters
            "u_cell_size": 10.0,
            "v_cell_size": 10.0,
            "w_cell_size": 10.0,
            "depth_core": 400.0,
            "minimum_level": 8,
            "max_distance": 200.0,
            "diagonal_balance": False,
            "padding_distance": 1500.0,
            "name": "test_gravity_plate_simulation",
            # Add model parameters
            "background": 1000.0,
            "overburden_property": 5.0,
            "thickness": 50.0,
            "plate_property": 2.0,
            "width": 100.0,
            "strike_length": 100.0,
            "dip_length": 100.0,
            "dip": 0.0,
            "dip_direction": 0.0,
            "number": 9,
            "spacing": 10.0,
            "elevation": 20,
        }
        ifile.set_values(**options_dict)

    with caplog.at_level(logging.WARNING):
        params = PlateSimulationOptions.build(ifile.to_params(workspace=geoh5))
    assert "Overburden thickness exceeds the plate depth" in caplog.text
    assert isinstance(params.simulation, SimPEGGroup)

    assert isinstance(params.mesh, MeshOptions)
    assert params.mesh.u_cell_size == 10.0
    assert params.mesh.v_cell_size == 10.0
    assert params.mesh.w_cell_size == 10.0
    assert params.mesh.depth_core == 400.0
    assert params.mesh.max_distance == 200.0
    assert params.mesh.padding_distance == 1500.0
    assert params.mesh.minimum_level == 8
    assert not params.mesh.diagonal_balance

    assert isinstance(params.model, ModelOptions)
    assert params.model.plate_options.name == "test_gravity_plate_simulation"
    assert params.model.background == 1000.0
    assert params.model.overburden_options.thickness == 50.0
    assert params.model.overburden_options.overburden_property == 5.0
    assert params.model.plate_options.plate_property == 2.0
    assert params.model.plate_options.geometry.strike_length == 100.0
    assert params.model.plate_options.geometry.dip_length == 100.0
    assert params.model.plate_options.geometry.dip == 0.0
    assert params.model.plate_options.geometry.direction == 0.0

    assert params.model.plate_options.number == 9
    assert params.model.plate_options.spacing == 10.0
    # reset by validator
    assert params.model.plate_options.geometry.elevation == 50.0
