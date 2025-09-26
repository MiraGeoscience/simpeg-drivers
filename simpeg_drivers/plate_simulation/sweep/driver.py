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
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json.input_file import InputFile

from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.options import SweepOptions
from simpeg_drivers.plate_simulation.sweep.uijson import PlateSweepUIJson


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


# TODO: Can we make this generic (PlateSweepDriver -> SweepDriver)?
class PlateSweepDriver(Driver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = SweepOptions

    def __init__(self, params: SweepOptions):
        super().__init__(params)

        self._out_group = self.validate_out_group(self.params.out_group)

    @property
    def out_group(self) -> SimPEGGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    def validate_out_group(self, out_group: SimPEGGroup | None) -> SimPEGGroup:
        """
        Validate or create a UIJsonGroup to store results.

        :param value: Output group from selection.
        """
        if isinstance(out_group, SimPEGGroup):
            return out_group

        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            out_group = SimPEGGroup.create(
                self.params.geoh5,
                name=self.params.title,
            )
            out_group.entity_type.name = self.params.title
            self.params = self.params.model_copy(update={"out_group": out_group})
            out_group.options = self.params.serialize()
            out_group.metadata = None

        return out_group

    @classmethod
    def start(cls, filepath: str | Path, mode="r", **_) -> Driver:
        """Start the parameter sweep from a ui.json file."""
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

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""

        trials = self.params.trials
        logger.info(
            "Running %d trials of %s . . .",
            len(trials),
            self.params.template.options["title"],
        )
        for kwargs in trials:
            options = dict(self.params.template_options, **kwargs)
            uid = SweepOptions.uuid_from_params(options)
            kwargs.update({"out_group": str(self.out_group.uid)})
            PlateSweepDriver.run_worker(
                uid, kwargs, self.workspace.h5file, self.params.workdir
            )

    @staticmethod
    def run_worker(uid: str, data: dict, h5file: Path, workdir: Path | None):
        if workdir is None:
            workdir = h5file.parent

        workerfile = workdir / f"{uid}.geoh5"
        if workerfile.exists():
            logger.info("Skipping trial %s, since the file already exists.", uid)
            return

        shutil.copy(h5file, workerfile)
        with Workspace(workerfile, mode="r+") as worker:
            plate_simulation = next(
                group
                for group in worker.groups
                if isinstance(group, SimPEGGroup | UIJsonGroup)
                and "plate_simulation.driver" in group.options.get("run_command")
            )

            ifile = InputFile(ui_json=plate_simulation.options, validate=False)
            for key, value in data.items():
                ifile.set_data_value(key, value)
            options = PlateSimulationOptions.build(
                ifile.data, geoh5=worker, out_group=plate_simulation
            )
            options.write_ui_json(workdir / f"{uid}.ui.json")
            PlateSimulationDriver.start(workdir / f"{uid}.ui.json")


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    PlateSweepDriver.start(file)
