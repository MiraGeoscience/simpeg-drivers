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
from geoapps_utils.utils.locations import topo_drape_elevation
from geoapps_utils.utils.logger import get_logger
from geoapps_utils.utils.transformations import rotate_xyz
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import AirborneTEMReceivers, Surface
from geoh5py.shared.utils import (
    fetch_active_workspace,
)
from geoh5py.ui_json.ui_json import BaseUIJson
from scipy.spatial import cKDTree
from typing_extensions import Self

from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.plate_simulation.match.options import MatchOptions


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


class PlateMatchDriver(BaseDriver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = MatchOptions

    def __init__(self, params: MatchOptions, workers: list[tuple[str]] | None = None):
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
        Validate or create a SimPEGGroup to store results.

        :param out_group: Output group from selection.
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

        tree = cKDTree(self.params.survey.vertices[:, :2])

        topo_z = (
            self.params.topography.values
            if self.params.topography.values is not None
            else self.params.topography_object.locations[:, 2]
        )
        topo_drape_z = topo_drape_elevation(
            self.params.survey.vertices,
            self.params.topography_object.locations,
            topo_z,
            triangulation=self.params.topography_object.cells
            if isinstance(self.params.topography_object, Surface)
            else None,
        )

        for ii, query in enumerate(self.params.queries.vertices):
            nearest = tree.query(query[:2], k=1)[0]
            line_mask = np.where(
                self.params.survey.parts == self.params.survey.parts[nearest]
            )[0]
            distances = np.linalg.norm(
                self.params.survey.vertices[nearest, :2]
                - self.params.survey.vertices[line_mask, :2],
                axis=1,
            )
            dist_mask = distances < self.params.max_distance
            indices = line_mask[dist_mask]

            # Compute local coordinates for the current line segment
            line_dist = distances[dist_mask]
            line_dist[indices < nearest] *= -1.0
            local_xyz = np.c_[
                line_dist,
                np.zeros_like(line_dist),
                self.params.survey.vertices[indices, 2] - topo_drape_z[indices],
            ]

            if self.params.strike_angles is not None:
                angle = self.params.strike_angles[ii]
                local_xyz = rotate_xyz(
                    local_xyz, [0, 0, 0], self.params.strike_angles[ii], 0
                )

            # Convert to polar coordinates (distance, azimuth, height)
            local_polar = np.c_[
                line_dist,
                90 - (np.rad2deg(np.arctan2(local_xyz[:, 0], local_xyz[:, 1])) % 180),
                local_xyz[:, 2],
            ]

            projection = None
            data = {}
            for file in self.params.simulations.iterdir():
                if Path(file).resolve().suffix == ".geoh5":
                    with Workspace(file, mode="r") as ws:
                        sim = next(
                            group
                            for group in ws.groups
                            if isinstance(group, SimPEGGroup) and "Plate" in group.name
                        )
                        fwr = next(
                            child
                            for child in sim.children
                            if isinstance(child, SimPEGGroup)
                        )
                        survey = next(
                            child
                            for child in fwr.children
                            if isinstance(child, AirborneTEMReceivers)
                        )
                        group = survey.get_entity("Iteration_0_z")[0]
                        data[Path(file).stem] = group.table()

                        # Create a projection matrix to interpolate simulated data to the observation locations
                        if projection is None:
                            dist = np.sign(survey.vertices[:, 0]) * np.linalg.norm(
                                survey.vertices[:, :2], axis=1
                            )
                            azm = (
                                90
                                - np.rad2deg(
                                    np.arctan2(
                                        survey.vertices[:, 0], survey.vertices[:, 1]
                                    )
                                )
                                % 180
                            ).round(decimals=1)
                            height = (survey.vertices[:, 2]).round(decimals=1)
                            polar_coordinates = np.c_[dist, height, azm]

                            shape = (-1, len(np.unique(azm)), len(np.unique(height)))
                            polar_coordinates.reshape(shape)


if __name__ == "__main__":
    # file = Path(sys.argv[1])
    file = Path(r"C:\Users\dominiquef\Documents\Workspace\Teck\RnD\plate_match.ui.json")
    PlateMatchDriver.start(file)
