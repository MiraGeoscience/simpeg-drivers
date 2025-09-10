# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import sys
from pathlib import Path

from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json.input_file import InputFile
from geoh5py.ui_json.ui_json import BaseUIJson

from simpeg_drivers import assets_path
from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.sweep.options import PlateSweepOptions
from simpeg_drivers.plate_simulation.sweep.uijson import PlateSweepUIJson


class PlateSweepDriver:
    def __init__(self, options: PlateSweepOptions):
        self.options = options

    @classmethod
    def start(cls, uijson: str | Path | BaseUIJson):
        if isinstance(uijson, str):
            uijson = Path(uijson).resolve()

        if isinstance(uijson, Path):
            uijson = PlateSweepUIJson.read(uijson)

        options = PlateSweepOptions.from_uijson(uijson)
        driver = cls(options=options)
        driver.run()

    def run(self):
        with fetch_active_workspace(self.options.geoh5) as geoh5:
            for kwargs in self.options.product:
                workpath = geoh5.h5file.parent
                uid = PlateSweepOptions.uuid_from_params(kwargs.values())
                h5file = workpath / f"{uid}.geoh5"
                if h5file.exists():
                    continue

                worker = geoh5.get_entity(self.options.worker)[0]
                with Workspace.create(h5file) as geoh5:
                    worker.copy(parent=geoh5, copy_relatives=True)
                    # TODO: I probably need to update the group options here
                    # TODO: Check that copy_relatives has worked for nested groups. There
                    #  should be a survey object in the new geoh5 file.

                    ifile = InputFile(ui_json=worker.options, validate=False)
                    for key, value in kwargs.items():
                        ifile.set_data_value(key, value)

                    worker.options = ifile.ui_json
                    ifile.write_ui_json(name=f"{id}.ui.json", path=workpath)
                    PlateSimulationDriver.start(workpath / f"{id}.ui.json")
                    assert True


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    PlateSweepDriver.start(PlateSweepUIJson(file))
