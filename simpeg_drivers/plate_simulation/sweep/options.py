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

import numpy as np
from geoapps_utils.base import Options
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, ValidationError
from typing_extensions import Self


class ParamSweep(BaseModel):
    name: str
    start: float
    stop: float
    count: int

    def __call__(self):
        return (self.start, self.stop, self.count)


class SweepOptions(Options):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

        def collect_sweep(param):
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
    def trials(self):
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
