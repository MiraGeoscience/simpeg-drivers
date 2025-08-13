# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile

from simpeg_drivers import assets_path
from simpeg_drivers.plate_simulation.driver import (
    PlateSimulationOptions,
)
from simpeg_drivers.plate_simulation.models.options import ModelOptions
from simpeg_drivers.plate_simulation.options import MeshOptions
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from simpeg_drivers.utils.testing_utils.options import (
    MeshOptions as SyntheticsMeshOptions,
)
from simpeg_drivers.utils.testing_utils.options import (
    ModelOptions as SyntheticsModelOptions,
)
from simpeg_drivers.utils.testing_utils.options import (
    SurveyOptions,
    SyntheticDataInversionOptions,
)
from simpeg_drivers.utils.testing_utils.runtests import setup_inversion_workspace


# pylint: disable=too-many-statements
def test_plate_simulation_params_from_input_file(tmp_path):
    opts = SyntheticDataInversionOptions(
        survey=SurveyOptions(n_stations=8, n_lines=8),
        mesh=SyntheticsMeshOptions(),
        model=SyntheticsModelOptions(anomaly=0.0),
    )
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path, method="gravity", options=opts
    )

    with geoh5.open() as ws:
        ifile = InputFile.read_ui_json(
            assets_path() / "uijson" / "plate_simulation.ui.json", validate=False
        )
        ifile.data["name"] = "test_gravity_plate_simulation"
        ifile.data["geoh5"] = ws

        # Add simulation parameter
        gravity_inversion = SimPEGGroup.create(ws)

        options = GravityForwardOptions.model_construct()
        fwr_ifile = InputFile.read_ui_json(options.default_ui_json)
        options_dict = fwr_ifile.ui_json
        options_dict["inversion_type"] = "gravity"
        options_dict["forward_only"] = True
        options_dict["geoh5"] = str(ws.h5file)
        options_dict["topography_object"]["value"] = str(topography.uid)
        options_dict["data_object"]["value"] = str(survey.uid)
        gravity_inversion.options = options_dict
        ifile.data["simulation"] = gravity_inversion

        # Add mesh parameters
        ifile.data["u_cell_size"] = 10.0
        ifile.data["v_cell_size"] = 10.0
        ifile.data["w_cell_size"] = 10.0
        ifile.data["depth_core"] = 400.0
        ifile.data["minimum_level"] = 8
        ifile.data["max_distance"] = 200.0
        ifile.data["diagonal_balance"] = False
        ifile.data["padding_distance"] = 1500.0

        # Add model parameters
        ifile.data["background"] = 1000.0
        ifile.data["overburden"] = 5.0
        ifile.data["thickness"] = 50.0
        ifile.data["plate"] = 2.0
        ifile.data["width"] = 100.0
        ifile.data["strike_length"] = 100.0
        ifile.data["dip_length"] = 100.0
        ifile.data["dip"] = 0.0
        ifile.data["dip_direction"] = 0.0
        ifile.data["number"] = 9
        ifile.data["spacing"] = 10.0
        ifile.data["relative_locations"] = True
        ifile.data["easting"] = 10.0
        ifile.data["northing"] = 10.0
        ifile.data["elevation"] = -250
        ifile.data["reference_surface"] = "topography"
        ifile.data["reference_type"] = "mean"

    params = PlateSimulationOptions.build(ifile)
    assert isinstance(params.simulation, SimPEGGroup)

    simulation_parameters = params.simulation_parameters()

    assert simulation_parameters.inversion_type == "gravity"
    assert simulation_parameters.forward_only
    assert simulation_parameters.geoh5.h5file == ws.h5file
    assert simulation_parameters.active_cells.topography_object.uid == topography.uid
    assert simulation_parameters.data_object.uid == survey.uid

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
    assert params.model.plate_model.name == "test_gravity_plate_simulation"
    assert params.model.background == 1000.0
    assert params.model.overburden_model.thickness == 50.0
    assert params.model.overburden_model.overburden == 5.0
    assert params.model.plate_model.plate == 2.0
    assert params.model.plate_model.width == 100.0
    assert params.model.plate_model.strike_length == 100.0
    assert params.model.plate_model.dip_length == 100.0
    assert params.model.plate_model.dip == 0.0
    assert params.model.plate_model.dip_direction == 0.0

    assert params.model.plate_model.number == 9
    assert params.model.plate_model.spacing == 10.0
    assert params.model.plate_model.relative_locations
    assert params.model.plate_model.easting == 10.0
    assert params.model.plate_model.northing == 10.0
    assert params.model.plate_model.elevation == -250.0
