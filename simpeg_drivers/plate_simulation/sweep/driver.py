# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import shutil
import sys
from numbers import Number
from pathlib import Path
from typing import Self

import numpy as np
from dask.distributed import Client
from geoapps_utils.base import Driver
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.logger import get_logger
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.utils import (
    dict_to_json_str,
    str_json_to_dict,
    uuid_from_values,
)
from geoh5py.ui_json.utils import flatten
from h5py import File
from pandas import DataFrame

from simpeg_drivers.driver import BaseDriver, validate_client, validate_workers
from simpeg_drivers.plate_simulation.driver import PlateSimulationDriver
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.plate_simulation.sweep.options import SweepOptions
from simpeg_drivers.utils.utils import start_dask_run, validate_out_group


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


class PlateSweepDriver(Driver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = SweepOptions

    def __init__(
        self,
        params: SweepOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
    ):
        super().__init__(params)

        self._out_group = validate_out_group(self.params)
        self._client: Client | bool = validate_client(client)
        self._workers: list[tuple[str]] = validate_workers(self._client, workers)

    def simpeg_run(self):
        """
        Run call to simpeg.
        """

    def start_message(self):
        """
        Starting message displayed by the logger.
        """

    @classmethod
    def start(cls, filepath: str | Path, mode="r", **_) -> Self:
        """
        Start the parameter sweep from a ui.json file.

        Force the mode to be read-only for safe copy.
        """
        return super().start(filepath, mode="r")

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""

        trials = self.params.trials
        logger.info(
            "Running %d trials of %s . . .",
            len(trials),
            self.params.template.options["title"],
        )

        use_futures = self._client

        if use_futures and trials:
            blocks = np.array_split(trials, len(self._workers))
        else:
            blocks = trials

        futures = []
        for ind, block in enumerate(blocks):
            if use_futures:
                futures.append(
                    self._client.submit(
                        run_block,
                        block,
                        self.params.geoh5.h5file,
                        self.params.workdir,
                        self._workers[ind],
                        workers=self._workers[ind],
                    )
                )

            else:
                run_block(
                    [block],
                    self.params.geoh5.h5file,
                    self.params.workdir,
                )

        if use_futures:
            self._client.gather(futures)

        if self.params.generate_summary:
            summary = generate_summary(self.params.workdir.iterdir())
            out_file = self.params.geoh5.h5file.parent / "summary.xlsx"
            summary.to_excel(out_file, index=False)
            with self.params.geoh5.open(mode="r+"):
                self._out_group.add_file(out_file)

    @staticmethod
    def run_trial(
        data: dict, h5file: Path, workdir: str, worker: tuple[str] | None = None
    ):
        """
        Run a single trial of the plate simulation with name encoding from the parameters.

        :param data: Dictionary of parameters for the trial.
        :param h5file: Path to the geoh5 file.
        :param workdir: Working directory to copy the geoh5 file to.
        :param worker: Dask.distributed.Worker to run the trial on.
        """
        json_string = dict_to_json_str(data)
        uid = uuid_from_values(json_string)

        workerdir = h5file.parent / workdir

        if not workerdir.exists():
            workerdir.mkdir(exist_ok=True)

        workerfile = workerdir / f"{uid}.geoh5"
        if workerfile.exists():
            logger.info("Skipping trial %s, since the file already exists.", uid)
            return

        shutil.copy(h5file, workerfile)
        with Workspace(workerfile, mode="r+") as workspace:
            plate_simulation = next(
                group
                for group in workspace.groups
                if isinstance(group, SimPEGGroup | UIJsonGroup)
                and (
                    "plate_simulation.driver" in group.options.get("run_command")
                    or "plate simulation" == group.options.get("inversion_type")
                )
            )

            opt_dict = workspace.promote(flatten(plate_simulation.options))
            opt_dict["geoh5"] = workspace
            opt_dict["out_group"] = None
            opt_dict["monitoring_directory"] = None
            opt_dict.update(data)
            options = PlateSimulationOptions.build(opt_dict)
            plate_sim = PlateSimulationDriver(options, workers=[worker])
            plate_sim.simulation_driver.logger = False
            # Knock out the log directive
            plate_sim.out_group.add_file(
                json_string.encode("utf-8"), name="options.txt"
            )
            plate_sim.run()

        del plate_sim
        return None

    @classmethod
    def start_dask_run(
        cls, json_path: Path, n_workers: int | None = None, n_threads: int | None = None
    ):
        """
        Runs plate sweep application with Dask optimization

        :param json_path: Path to input file (.ui.json) for the application.
        :param n_workers: Number of workers to use.
        :param n_threads: Number of threads to use.
        """
        start_dask_run(cls, json_path, n_workers=n_workers, n_threads=n_threads)


def forms_to_values(data: dict) -> dict:
    """
    Convert a dictionary of forms to a dictionary of values, where the value is a number.

    :param data: Dictionary of forms.

    :return: Dictionary of key and numeric values
    """
    fields = {}
    for name, form in data.items():
        if isinstance(form, dict) and isinstance(form.get("value"), Number):
            fields[name] = form.get("value")

    return fields


def generate_summary(directory: list[Path]) -> DataFrame:
    """
    Generate a summary of the trials and save it to the geoh5 file.

    :param directory: List of paths to geoh5 files to summarize.

    :return: Dataframe of trial names and options.
    """
    summary = []
    for simulation in directory:
        if Path(simulation).resolve().suffix != ".geoh5":
            continue

        with File(simulation, mode="r") as geoh5:
            for group in geoh5["GEOSCIENCE"]["Groups"].values():
                if group.get("options", None):
                    options = str_json_to_dict(np.r_[group["options"]][0])

                    if (
                        options["title"] == "Plate Simulation"
                        and len(group["Objects"]) > 0
                    ):
                        options = forms_to_values(options)
                        output = {"file": simulation.stem}
                        output.update(options)
                        summary.append(output)
                        break

    return DataFrame(summary)


def run_block(
    trials: list[dict],
    h5file: Path,
    workdir: str,
    worker: tuple[str] | None = None,
):
    """
    Loop through a list of trials and run a worker for each unique parameter set.
    """
    for kwargs in trials:
        PlateSweepDriver.run_trial(kwargs, h5file, workdir, worker=worker)


if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateSweepDriver.start_dask_run(file)
