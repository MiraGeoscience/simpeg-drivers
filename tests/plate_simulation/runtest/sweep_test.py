# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile

from simpeg_drivers import assets_path
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.driver import PlateSweepDriver
from simpeg_drivers.plate_simulation.sweep.options import SweepOptions
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from simpeg_drivers.utils.synthetics.options import SurveyOptions
from simpeg_drivers.utils.synthetics.surveys.factory import get_survey
from simpeg_drivers.utils.synthetics.topography import get_topography_surface


def setup_plate_sweep(workspace) -> SimPEGGroup:
    survey_options = SurveyOptions()
    data = get_survey(workspace, method="gravity", options=survey_options)
    topo = get_topography_surface(workspace, survey_options)

    gravity = SimPEGGroup.create(workspace, name="gravity fwd")
    options = GravityForwardOptions.model_construct()
    fwr_ifile = InputFile.read_ui_json(options.default_ui_json)
    options_dict = fwr_ifile.ui_json
    options_dict["inversion_type"] = "gravity"
    options_dict["forward_only"] = True
    options_dict["geoh5"] = str(workspace.h5file)
    options_dict["topography_object"]["value"] = str(topo.uid)
    options_dict["data_object"]["value"] = str(data.uid)
    options_dict["out_group"]["value"] = str(gravity.uid)
    gravity.options = options_dict

    simulation = SimPEGGroup.create(workspace, name="plate simulation")
    options = PlateSimulationOptions.model_construct()
    plate_ifile = InputFile.read_ui_json(options.default_ui_json)
    options_dict = plate_ifile.ui_json
    options_dict["simulation"]["value"] = str(gravity.uid)
    options_dict["overburden"]["value"] = 100.0
    options_dict["thickness"]["value"] = 20.0
    options_dict["u_cell_size"]["value"] = 10.0
    options_dict["v_cell_size"]["value"] = 10.0
    options_dict["w_cell_size"]["value"] = 10.0
    options_dict["depth_core"]["value"] = 400.0
    options_dict["minimum_level"]["value"] = 8
    options_dict["max_distance"]["value"] = 200.0
    options_dict["diagonal_balance"]["value"] = False
    options_dict["padding_distance"]["value"] = 1500.0
    options_dict["dip_direction"]["value"] = 0.0
    options_dict["number"]["value"] = 1
    options_dict["relative_locations"]["value"] = True
    options_dict["easting"]["value"] = 10.0
    options_dict["northing"]["value"] = 10.0
    options_dict["elevation"]["value"] = -250.0
    options_dict["reference_surface"]["value"] = "topography"
    options_dict["reference_type"]["value"] = "mean"
    options_dict["out_group"]["value"] = str(simulation.uid)
    simulation.options = options_dict

    return simulation


def test_sweep(tmp_path):
    workdir = tmp_path / "my_workdir"

    with Workspace.create(tmp_path / "test.geoh5") as ws:
        plate_simulation = setup_plate_sweep(ws)

        ifile = InputFile.read_ui_json(
            assets_path() / "uijson" / "plate_sweep.ui.json", validate=False
        )
        ifile.data["name"] = "test_gravity_plate_simulation"
        ifile.data["geoh5"] = ws
        ifile.data["template"] = str(plate_simulation.uid)
        ifile.data["workdir"] = str(workdir)
        ifile.data["background_start"] = 0.0
        ifile.data["background_stop"] = 100.0
        ifile.data["background_count"] = 2
        ifile.data["plate_start"] = 500.0
        ifile.data["plate_stop"] = 1000.0
        ifile.data["plate_count"] = 2
        ifile.data["out_group"] = None

        ifile.write_ui_json(name="plate_sweep.ui.json", path=tmp_path)
    PlateSweepDriver.start(tmp_path / "plate_sweep.ui.json")

    assert workdir.exists()

    with Workspace(tmp_path / "test.geoh5"):
        ifile = InputFile.read_ui_json(tmp_path / "plate_sweep.ui.json")
        ifile.set_data_value("background_count", 3)
        ifile.write_ui_json(path=tmp_path, name="plate_sweep_modified.ui.json")

    PlateSweepDriver.start(tmp_path / "plate_sweep_modified.ui.json")

    n = len(list(workdir.glob("*.geoh5")))
    assert n == 6
