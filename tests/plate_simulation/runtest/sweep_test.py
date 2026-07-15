# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import UIJson
from pandas import read_excel

from simpeg_drivers import assets_path
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.driver import PlateSweepDriver
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from simpeg_drivers.utils.synthetics.options import SyntheticsComponentsOptions
from simpeg_drivers.utils.synthetics.surveys.factory import get_survey
from simpeg_drivers.utils.synthetics.topography import get_topography_surface


def setup_plate_sweep(workspace) -> SimPEGGroup:
    options = SyntheticsComponentsOptions()
    data = get_survey(workspace, method="gravity", options=options.survey)
    topo = get_topography_surface(workspace, options)

    options = GravityForwardOptions.model_construct()
    fwr_file = UIJson.read(options.default_ui_json)

    fwr_file.inversion_type = "gravity"
    fwr_file.forward_only = True
    fwr_file.geoh5 = str(workspace.h5file)
    fwr_file.topography_object.value = str(topo.uid)
    fwr_file.data_object.value = str(data.uid)

    gravity = fwr_file.to_ui_json_group(workspace=workspace, name="gravity fwd")

    options = PlateSimulationOptions.model_construct()
    plate_ifile = UIJson.read(options.default_ui_json)

    plate_ifile.simulation.value = str(gravity.uid)
    plate_ifile.overburden_property.value = 100.0
    plate_ifile.thickness.value = 20.0
    plate_ifile.u_cell_size.value = 10.0
    plate_ifile.v_cell_size.value = 10.0
    plate_ifile.w_cell_size.value = 10.0
    plate_ifile.depth_core.value = 400.0
    plate_ifile.minimum_level.value = 8
    plate_ifile.max_distance.value = 200.0
    plate_ifile.diagonal_balance.value = False
    plate_ifile.padding_distance.value = 1500.0
    plate_ifile.dip_direction.value = 0.0
    plate_ifile.number.value = 1
    plate_ifile.elevation.value = 100.0

    simulation = plate_ifile.to_ui_json_group(
        workspace=workspace, name="plate simulation"
    )

    return simulation


def test_sweep(tmp_path):
    workdir = tmp_path / "my_workdir"

    with Workspace.create(tmp_path / "test.geoh5") as ws:
        plate_simulation = setup_plate_sweep(ws)

        ifile = UIJson.read(assets_path() / "uijson" / "plate_sweep.ui.json")
        data = {
            "name": "test_gravity_plate_simulation",
            "geoh5": ws,
            "template": str(plate_simulation.uid),
            "workdir": str(workdir),
            "background_start": 0.0,
            "background_stop": 100.0,
            "background_count": 2,
            "plate_start": 500.0,
            "plate_stop": 1000.0,
            "plate_count": 2,
            "out_group": None,
        }
        ifile.set_values(**data)
        ifile.write(tmp_path / "plate_sweep.ui.json")
    PlateSweepDriver.start(tmp_path / "plate_sweep.ui.json")

    assert workdir.exists()

    with Workspace(tmp_path / "test.geoh5"):
        ifile = UIJson.read(tmp_path / "plate_sweep.ui.json")
        ifile.set_values(background_count=3)
        ifile.write(tmp_path / "plate_sweep_modified.ui.json")

    PlateSweepDriver.start(tmp_path / "plate_sweep_modified.ui.json")

    n = len(list(workdir.glob("*.geoh5")))
    assert n == 6

    xls = read_excel(tmp_path / "summary.xlsx")

    assert len(xls) == 6
