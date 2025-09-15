# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import shutil
import sys
from pathlib import Path

from geoapps_utils.base import Driver
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.logger import get_logger
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
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
    def start(cls, filepath: str | Path, mode="r", **kwargs) -> Driver:
        _ = kwargs
        logger.info("Loading input file . . .")
        filepath = Path(filepath).resolve()
        uijson = PlateSweepUIJson.read(filepath)

        with Workspace(uijson.geoh5, mode=mode) as workspace:
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

    @property
    def out_group(self):
        """The SimPEGGroup"""
        if self._out_group is None:
            if self.params.out_group is not None:
                self._out_group = self.params.out_group
                return self._out_group

            with fetch_active_workspace(self.workspace, mode="r+"):
                self._out_group = SimPEGGroup.create(
                    self.params.geoh5, name="Plate Sweep"
                )
                self._out_group.options = self.params.serialize()

        return self._out_group

    def run(self):
        for kwargs in self.params.trials:
            uid = SweepOptions.uuid_from_params(kwargs.values())
            PlateSweepDriver.run_worker(
                uid, kwargs, self.workspace.h5file, self.out_group
            )

    @staticmethod
    def run_worker(uid, data, workspace_path, out_group):
        # Eventually will take the path from the options set by user
        workpath = workspace_path.parent
        h5file = workpath / f"{uid}.geoh5"
        if h5file.exists():
            return

        shutil.copy(workspace_path, h5file)
        with Workspace(h5file, mode="r+") as geoh5:
            with fetch_active_workspace(out_group.workspace, mode="r+"):
                out_group = out_group.copy(parent=geoh5)

                plate_simulation = next(
                    group
                    for group in geoh5.groups
                    if isinstance(group, SimPEGGroup)
                    and "plate_simulation" in group.options.get("run_command")
                )

                ifile = InputFile(ui_json=plate_simulation.options, validate=False)
                for key, value in data.items():
                    ifile.set_data_value(key, value)

                options = PlateSimulationOptions.build(
                    ifile.data, geoh5=geoh5, out_group=plate_simulation
                )
                options.write_ui_json(workpath / f"{uid}.ui.json")
                out_group.options["simulation"]["value"] = str(options.out_group.uid)
                PlateSimulationDriver.start(workpath / f"{uid}.ui.json")


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    PlateSweepDriver.start(file)
