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
from geoh5py import Workspace
from pydantic import BaseModel, ConfigDict

from simpeg_drivers.plate_simulation.sweep.uijson import PlateSweepUIJson


class ParamSweep(BaseModel):
    name: str
    start: float
    stop: float
    count: int

    def __call__(self):
        return (self.start, self.stop, self.count)


class PlateSweepOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    geoh5: Workspace
    worker: uuid.UUID
    sweeps: list[ParamSweep]

    @classmethod
    def from_uijson(cls, uijson: PlateSweepUIJson):
        return cls(**uijson.to_params())

    @property
    def product(self):
        names = [s.name for s in self.sweeps]
        iterations = itertools.product(*[np.linspace(*s()) for s in self.sweeps])
        return [dict(zip(names, i, strict=False)) for i in iterations]

    @staticmethod
    def uuid_from_params(params: tuple) -> str:
        """
        Create a deterministic uuid.

        :param params: Tuple containing the values of a sweep iteration.

        :returns: Unique but recoverable uuid file identifier string.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(hash(params))))
