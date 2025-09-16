# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import itertools
import uuid
from pathlib import Path
from typing import ClassVar

import numpy as np
from geoapps_utils.base import Options
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, ValidationError
from typing_extensions import Self

from simpeg_drivers import assets_path


class ParamSweep(BaseModel):
    """
    Data store for the sweep of a single parameter.

    :param name: Name of the parameter to sweep.
    :param start: Starting value of the parameter.
    :param stop: Ending value of the parameter.
    :param count: Number of values to sample between start and stop.
    """

    name: str
    start: float
    stop: float
    count: int

    def __call__(self) -> tuple[float, float, int]:
        return (self.start, self.stop, self.count)


class SweepOptions(Options):
    """
    Options for sweeping parameters within a template application.

    :param template: A SimPEGGroup containing the template for running an application.
        Any unswept parameters required by the application must be set on the groups
        options.  Any swept parameters will take priority over those set on the groups
        options.
    :param sweeps:  Sweep parameters to be combined to create a series of trials run
        by the template application.
    """

    name: ClassVar[str] = "plate_sweep"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/plate_sweep.ui.json"
    title: ClassVar[str] = "Plate Sweep"
    run_command: ClassVar[str] = "simpeg_drivers.plate_simulation.sweep.driver"
    out_group: SimPEGGroup | None = None
    template: SimPEGGroup
    sweeps: list[ParamSweep]

    @classmethod
    def build(cls, input_data: InputFile | dict | None = None, **kwargs) -> Self:
        """
        Build a dataclass from a dictionary or InputFile.

        :param input_data: Dictionary of parameters and values.

        :return: Dataclass of application parameters.
        """
        data = input_data or {}
        if isinstance(input_data, InputFile) and input_data.data is not None:
            data = input_data.data.copy()

        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary or InputFile.")

        data.update(kwargs)
        options = Options.collect_input_from_dict(cls, data)  # type: ignore

        def collect_sweep(param: str) -> dict:
            return {
                "name": param,
                "start": options.get(f"{param}_start"),
                "stop": options.get(f"{param}_stop"),
                "count": options.get(f"{param}_count"),
            }

        sweep_params = [k.removesuffix("_start") for k in options if "_start" in k]
        options["sweeps"] = [collect_sweep(param) for param in sweep_params]

        try:
            out = cls(**options)
        except ValidationError as errors:
            summary = "\n - ".join(
                f"{'.'.join(str(loc) for loc in error['loc'])}: "
                f"{error['msg']} for value -> {error['input']}"
                for error in errors.errors()
            )

            raise GeoAppsError(
                f"Invalid input data for {cls.__name__}:\n - {summary}"
            ) from errors

        if isinstance(input_data, InputFile):
            out._input_file = input_data

        return out

    @property
    def trials(self) -> list[dict]:
        """Returns a list of parameter combinations to run for each trial."""
        names = [s.name for s in self.sweeps]
        iterations = itertools.product(*[np.linspace(*s()) for s in self.sweeps])
        return [dict(zip(names, i, strict=True)) for i in iterations]

    @staticmethod
    def uuid_from_params(params: tuple) -> str:
        """
        Create a deterministic uuid.

        :param params: Tuple containing the values of a sweep iteration.

        :returns: Unique but recoverable uuid file identifier string.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(hash(params))))
