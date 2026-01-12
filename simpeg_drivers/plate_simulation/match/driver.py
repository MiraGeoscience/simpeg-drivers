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

import sys
from pathlib import Path

import numpy as np
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.logger import get_logger
from geoh5py import Workspace
from geoh5py.groups import UIJsonGroup
from geoh5py.shared.utils import (
    dict_to_json_str,
    fetch_active_workspace,
    uuid_from_values,
)
from geoh5py.ui_json.ui_json import BaseUIJson
from geoh5py.ui_json.utils import flatten
from typing_extensions import Self

from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.plate_simulation.match.options import MatchOptions


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


# TODO: Can we make this generic (PlateMatchDriver -> MatchDriver)?
class PlateMatchDriver(BaseDriver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = MatchOptions

    def __init__(self, params: MatchOptions, workers: list[tuple[str]] | None = None):
        super().__init__(params, workers=workers)

        self.out_group = self.validate_out_group(self.params.out_group)

    @property
    def out_group(self) -> UIJsonGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    @out_group.setter
    def out_group(self, value: UIJsonGroup):
        if not isinstance(value, UIJsonGroup):
            raise TypeError("Output group must be a UIJsonGroup.")

        if self.params.out_group != value:
            self.params.out_group = value
            self.params.update_out_group_options()

        self._out_group = value

    def validate_out_group(self, out_group: UIJsonGroup | None) -> UIJsonGroup:
        """
        Validate or create a UIJsonGroup to store results.

        :param value: Output group from selection.
        """
        if isinstance(out_group, UIJsonGroup):
            return out_group

        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            out_group = UIJsonGroup.create(
                self.params.geoh5,
                name=self.params.title,
            )
            out_group.entity_type.name = self.params.title

        return out_group

    @classmethod
    def start(cls, filepath: str | Path, mode="r", **_) -> Self:
        """Start the parameter matching from a ui.json file."""
        logger.info("Loading input file . . .")
        filepath = Path(filepath).resolve()
        uijson = BaseUIJson.read(filepath)

        with Workspace(uijson.geoh5, mode=mode) as workspace:
            try:
                options = MatchOptions.build(uijson.to_params(workspace=workspace))
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

        logger.info(
            "Running %s . . .",
            self.params.template.options["title"],
        )


if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateMatchDriver.start(file)
