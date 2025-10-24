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
from pathlib import Path
from typing import ClassVar

import numpy as np
from geoapps_utils.base import Options
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.utils import stringify
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, field_serializer

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
    stop: float | None
    count: int | None

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

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    name: ClassVar[str] = "plate_sweep"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/plate_sweep.ui.json"
    title: ClassVar[str] = "Plate Sweep"
    run_command: ClassVar[str] = "simpeg_drivers.plate_simulation.sweep.driver"
    out_group: SimPEGGroup | None = None
    forward_only: bool = True
    inversion_type: str = "plate sweep"
    template: SimPEGGroup | UIJsonGroup
    sweeps: list[ParamSweep]
    workdir: str = "./simulations"

    @field_serializer("sweeps")
    def sweeps_to_params(self, sweeps):
        out = {}
        for sweep in sweeps:
            if sweep.stop is not None and sweep.count < 2:
                out[f"{sweep.name}_start"] = sweep.start
                continue
            for key, value in sweep.model_dump().items():
                if key == "name":
                    continue
                out[f"{sweep.name}_{key}"] = value
        return out

    @field_serializer("workdir")
    def workdir_to_string(self, workdir):
        return str(workdir)

    @staticmethod
    def collect_input_from_dict(model: type[BaseModel], data: dict):
        """
        Recursively replace BaseModel objects with nested dictionary of 'data' values.

        Also collects sweep parameters into a list of ParamSweep objects.

        :param base_model: BaseModel object to structure data for.
        :param data: Flat dictionary of parameters and values without nesting structure
            and with sweep parameters collected into list.
        """
        options = Options.collect_input_from_dict(model, data)

        def collect_sweep(param: str) -> dict:
            return {
                "name": param,
                "start": options.pop(f"{param}_start"),
                "stop": options.pop(f"{param}_stop"),
                "count": options.pop(f"{param}_count"),
            }

        sweep_params = [k.removesuffix("_start") for k in options if "_start" in k]
        options["sweeps"] = [collect_sweep(param) for param in sweep_params]

        return options

    @property
    def trials(self) -> list[dict]:
        """Returns a list of parameter combinations to run for each trial."""
        names = [s.name for s in self.sweeps]
        iterations = itertools.product(*[np.linspace(*s()) for s in self.sweeps])
        options_dict = self.template_options.copy()

        trials = []
        for iterate in iterations:
            options_dict.update(dict(zip(names, iterate, strict=True)))
            trials.append(options_dict.copy())

        return trials

    @staticmethod
    def all_hashable_options(options: dict) -> dict:
        """Recurses through UIJson options to return flat dictionary of all key/values."""

        # TODO: Use the base UIJson to read options and flatten instead of
        #  InputFile.  Requires GEOPY-1875.

        ifile = InputFile(ui_json=options, validate=False)
        exceptions = list(Options.model_fields) + ["version", "icon", "documentation"]
        # TODO: add these to the Options fields with empty string defaults.
        out = {}
        for k, v in ifile.data.items():
            if k in exceptions:
                continue

            if isinstance(v, SimPEGGroup | UIJsonGroup):
                opts = v.options
                opts["geoh5"] = options["geoh5"]
                out.update(SweepOptions.all_hashable_options(opts))
            else:
                out[k] = v

        return out

    @property
    def template_options(self):
        """Return a flat version of the template.options dictionary."""
        options = self.template.options
        options["geoh5"] = self.geoh5
        return stringify(SweepOptions.all_hashable_options(options))
