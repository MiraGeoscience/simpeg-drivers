# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import contextlib
import cProfile
import pstats
import shutil
import sys
from pathlib import Path

import numpy as np
from dask.distributed import Client, LocalCluster, get_client, performance_report
from geoapps_utils.run import load_ui_json_as_dict
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.logger import get_logger
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.utils import fetch_active_workspace, stringify
from geoh5py.ui_json.input_file import InputFile
from geoh5py.ui_json.utils import flatten

from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.options import SweepOptions
from simpeg_drivers.plate_simulation.sweep.uijson import PlateSweepUIJson


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


# TODO: Can we make this generic (PlateSweepDriver -> SweepDriver)?
class PlateSweepDriver(BaseDriver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = SweepOptions

    def __init__(self, params: SweepOptions, workers: list[tuple[str]] | None = None):
        super().__init__(params, workers=workers)

        self.out_group = self.validate_out_group(self.params.out_group)

    @property
    def out_group(self) -> SimPEGGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    @out_group.setter
    def out_group(self, value: SimPEGGroup):
        if not isinstance(value, SimPEGGroup):
            raise TypeError("Output group must be a SimPEGGroup.")

        if self.params.out_group != value:
            self.params.out_group = value
            self.params.update_out_group_options()

        self._out_group = value

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

        return out_group

    @classmethod
    def start(cls, filepath: str | Path, mode="r", **kwargs) -> BaseDriver:
        """Start the parameter sweep from a ui.json file."""
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

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""

        trials = self.params.trials
        logger.info(
            "Running %d trials of %s . . .",
            len(trials),
            self.params.template.options["title"],
        )

        use_futures = self.client

        if use_futures:
            blocks = np.array_split(trials, len(self.workers))
        else:
            blocks = trials

        futures = []
        for ind, block in enumerate(blocks):
            if use_futures:
                futures.append(
                    self.client.submit(
                        trial_runs,
                        block,
                        self.params.geoh5.h5file,
                        self.params.workdir,
                        self.workers[ind],
                        workers=self.workers[ind],
                    )
                )

            else:
                trial_runs(
                    [block],
                    self.params.geoh5.h5file,
                    self.params.workdir,
                )

        if use_futures:
            self.client.gather(futures)

    @staticmethod
    def run_trial(
        data: dict, h5file: Path, workdir: Path | None, worker: tuple[str] | None = None
    ):
        uid = SweepOptions.uuid_from_params(data)

        if workdir is None:
            workdir = h5file.parent

        workerfile = workdir / f"{uid}.geoh5"
        if workerfile.exists():
            logger.info("Skipping trial %s, since the file already exists.", uid)
            return

        shutil.copy(h5file, workerfile)
        with Workspace(workerfile, mode="r+") as workspace:
            plate_simulation = next(
                group
                for group in workspace.groups
                if isinstance(group, SimPEGGroup | UIJsonGroup)
                and "plate_simulation.driver" in group.options.get("run_command")
            )

            opt_dict = workspace.promote(flatten(plate_simulation.options))
            opt_dict["geoh5"] = workspace
            opt_dict["out_group"] = None
            opt_dict.update(data)
            options = PlateSimulationOptions.build(opt_dict)
            plate_sim = PlateSimulationDriver(options, workers=[worker])
            plate_sim.run()

        del plate_sim
        return None


def trial_runs(
    trials: list[dict],
    h5file: Path,
    workdir: Path | None,
    worker: tuple[str] | None = None,
):
    """
    Loop through a list of trials and run a worker for each unique parameter set.
    """
    for kwargs in trials:
        PlateSweepDriver.run_trial(kwargs, h5file, workdir, worker=worker)


if __name__ == "__main__":
    file = Path(r"C:\Users\dominiquef\Desktop\Tests\GEOPY-2466.ui.json").resolve()

    input_file = load_ui_json_as_dict(file)
    n_workers = input_file.get("n_workers", None)
    n_threads = input_file.get("n_threads", None)
    save_report = input_file.get("performance_report", False)

    cluster = (
        LocalCluster(processes=True, n_workers=n_workers, threads_per_worker=n_threads)
        if ((n_workers is not None and n_workers > 1) or n_threads is not None)
        else None
    )
    profiler = cProfile.Profile()
    profiler.enable()

    with (
        cluster.get_client()
        if cluster is not None
        else contextlib.nullcontext() as client
    ):
        # Full run
        with (
            performance_report(filename=file.parent / "dask_profile.html")
            if (save_report and isinstance(client, Client))
            else contextlib.nullcontext()
        ):
            PlateSweepDriver.start(file)
            sys.stdout.close()

    profiler.disable()

    if save_report:
        with open(file.parent / "runtime_profile.txt", encoding="utf-8", mode="w") as s:
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats("cumulative")
            ps.print_stats()
