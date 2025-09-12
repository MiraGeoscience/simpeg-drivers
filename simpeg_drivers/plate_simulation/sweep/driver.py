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

from geoapps_utils.base import Driver
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.logger import get_logger
from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json.input_file import InputFile

from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.options import SweepOptions
from simpeg_drivers.plate_simulation.sweep.uijson import PlateSweepUIJson


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


# TODO: Can we make this generic (PlateSweepDriver -> SweepDriver)?
class PlateSweepDriver(Driver):
    _params_class = SweepOptions

    @classmethod
    def start(cls, filepath: str | Path, mode="r+", **kwargs) -> Driver:
        _ = kwargs
        logger.info("Loading input file . . .")
        filepath = Path(filepath).resolve()
        uijson = PlateSweepUIJson.read(filepath)

        with Workspace(uijson.geoh5) as workspace:
            try:
                options = SweepOptions.build(uijson.to_params(workspace=workspace))
                logger.info("Initializing application . . .")
                driver = cls(options)
                logger.info("Running application . . .")
                driver.run()
                logger.info("Results saved to %s", options.geoh5.h5file)

            except GeoAppsError as error:
                logger.warning("\n\nApplicationError: %s\n\n", error)
                sys.exit(1)

        return driver

    def run(self):
        for kwargs in self.params.trials:
            uid = SweepOptions.uuid_from_params(kwargs.values())
            ifile = InputFile(ui_json=self.params.template.options, validate=False)
            for key, value in kwargs.items():
                ifile.set_data_value(key, value)
            PlateSweepDriver.run_worker(uid, ifile.data, self.params.template)

    @staticmethod
    def run_worker(uid, data, out_group):
        # create files and run plate simulation, switch geoh5

        workpath = data["geoh5"].h5file.parent
        h5file = workpath / f"{uid}.geoh5"
        if h5file.exists():
            return

        with Workspace.create(h5file, mode="r+") as geoh5:
            with fetch_active_workspace(out_group.workspace):
                out_group.copy(parent=geoh5, copy_relatives=True)
            data["geoh5"] = geoh5
            options = PlateSimulationOptions.build(data)
            filepath = workpath / f"{uid}.ui.json"
            options.write_ui_json(filepath)
            PlateSimulationDriver.start(filepath)


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    PlateSweepDriver.start(PlateSweepUIJson.read(file))
