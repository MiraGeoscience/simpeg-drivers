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
from geoapps_utils.utils.plotting import symlog
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.objects import AirborneTEMReceivers, Surface
from geoh5py.shared.utils import (
    fetch_active_workspace,
)
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.ui_json import BaseUIJson
from scipy import signal
from scipy.sparse import csr_matrix, diags
from scipy.spatial import cKDTree
from tqdm import tqdm
from typing_extensions import Self

from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.plate_simulation.match.options import MatchOptions
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions


# import matplotlib.pyplot as plt

logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


class PlateMatchDriver(BaseDriver):
    """Sets up and manages workers to run all combinations of swepts parameters."""

    _params_class = MatchOptions

    def __init__(self, params: MatchOptions, workers: list[tuple[str]] | None = None):
        super().__init__(params, workers=workers)

        self._drape_heights = self.set_drape_height()

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
    def start(cls, filepath: str | Path, mode="r+", **_) -> Self:
        """Start the parameter matching from a ui.json file."""
        logger.info("Loading input file . . .")
        filepath = Path(filepath).resolve()
        # uijson = BaseUIJson.read(filepath)
        uijson = InputFile.read_ui_json(filepath)

        with uijson.geoh5.open(mode=mode):
            try:
                options = MatchOptions.build(uijson)
                logger.info("Initializing application . . .")
                driver = cls(options)
                logger.info("Running application . . .")
                driver.run()
                logger.info("Results saved to %s", options.geoh5.h5file)

            except GeoAppsError as error:
                logger.warning("\n\nApplicationError: %s\n\n", error)
                sys.exit(1)

        return driver

    def set_drape_height(self) -> np.ndarray:
        """Set drape heights based on topography object and optional topography data."""

        topo = self.params.topography_object.locations

        if self.params.topography is not None:
            topo[:, 2] = self.params.topography.values

        topo_drape_z = topo_drape_elevation(
            self.params.survey.vertices,
            topo,
            triangulation=self.params.topography_object.cells
            if isinstance(self.params.topography_object, Surface)
            else None,
        )
        return topo_drape_z[:, 2]

    def normalized_data(self, property_group: PropertyGroup, threshold=5) -> np.ndarray:
        """
        Return data from a property group with symlog scaling and zero mean.

        :param property_group: Property group containing data channels.
        :param threshold: Percentile threshold for symlog normalization.

        :return: Normalized data array.
        """
        table = property_group.table()
        data_array = np.vstack([table[name] for name in table.dtype.names])
        thresh = np.percentile(np.abs(data_array), threshold)
        log_data = symlog(data_array, thresh)
        return log_data - np.mean(log_data, axis=1)[:, None]

    def fetch_survey(self, workspace: Workspace) -> AirborneTEMReceivers | None:
        """Fetch the survey from the workspace."""
        for group in workspace.groups:
            if isinstance(group, SimPEGGroup):
                for child in group.children:
                    if isinstance(child, AirborneTEMReceivers):
                        return child

        return None

    def spatial_interpolation(
        self,
        indices: np.ndarray,
        locations: np.ndarray,
        strike_angle: float | None = None,
    ) -> csr_matrix:
        """
        Create a spatial interpolation matrix from simulation to observation locations.

        :param indices: Indices for the line segment of the observation locations.
        :param locations: Positions to interpolate from.
        :param strike_angle: Optional strike angle to correct azimuths.

        :return: Spatial interpolation matrix.
        """
        # Compute local coordinates for the current line segment
        local_polar = self.xyz_to_polar(self.params.survey.vertices[indices, :])
        local_polar[:, 1] = (
            0.0 if strike_angle is None else strike_angle
        )  # Align azimuths to zero

        # Convert to polar coordinates (distance, azimuth, height)
        query_polar = self.xyz_to_polar(locations)

        # Get the 8 nearest neighbors in the simulation to each observation point
        sim_tree = cKDTree(query_polar)
        rad, inds = sim_tree.query(local_polar, k=8)

        weights = (rad**2.0 + 1e-1) ** -1
        row_ids = np.kron(np.arange(local_polar.shape[0]), np.ones(8))
        inv_dist_op = csr_matrix(
            (weights.flatten(), (row_ids, np.hstack(inds.flatten()))),
            shape=(local_polar.shape[0], locations.shape[0]),
        )

        # Normalize the rows
        row_sum = np.asarray(inv_dist_op.sum(axis=1)).flatten() ** -1.0
        return diags(row_sum) @ inv_dist_op

    @staticmethod
    def xyz_to_polar(xyz: np.ndarray) -> np.ndarray:
        """
        Convert Cartesian coordinates to polar coordinates defined as
        (distance, azimuth, height), where distance is signed based on the
        x-coordinate relative to the mean location.

        :param xyz: Cartesian coordinates.

        :return: Polar coordinates (distance, azimuth, height).
        """
        mean_loc = np.mean(xyz, axis=0)
        distances = np.sign(xyz[:, 0] - mean_loc[0]) * np.linalg.norm(
            xyz[:, :2] - mean_loc[:2], axis=1
        )

        azimuths = 90 - (np.rad2deg(np.arctan2(xyz[:, 0], xyz[:, 1])) % 180)
        return np.c_[distances, azimuths, xyz[:, 2]]

    @staticmethod
    def time_interpolation(
        query_times: np.ndarray, sim_times: np.ndarray
    ) -> csr_matrix:
        """
        Create a time interpolation matrix from simulation to observation times.

        :param query_times: Observation times.
        :param sim_times: Simulation times.

        :return: Time interpolation matrix.
        """
        right = np.searchsorted(sim_times, query_times)

        inds = np.r_[right - 1, right]

        row_ids = np.tile(np.arange(len(query_times)), 2)
        weights = (np.abs(query_times[row_ids] - sim_times[inds]) + 1e-12) ** -1

        time_projection = csr_matrix(
            (weights.flatten(), (row_ids, np.hstack(inds.flatten()))),
            shape=(len(query_times), len(sim_times)),
        )
        row_sum = np.asarray(time_projection.sum(axis=1)).flatten() ** -1.0
        return diags(row_sum) @ time_projection

    def get_segment_indices(self, nearest: int) -> np.ndarray:
        """
        Get indices of line segment for a given nearest vertex.

        :param nearest: Nearest vertex index.
        """
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
        return indices

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""

        logger.info(
            "Running %s . . .",
            self.params.title,
        )
        observed = self.normalized_data(self.params.data)

        scores = []
        files_id = []
        tree = cKDTree(self.params.survey.vertices[:, :2])
        spatial_projection = None
        time_projection = None
        for ii, query in enumerate(self.params.queries.vertices):
            for sim_file in tqdm(self.params.simulation_files):
                with Workspace(sim_file, mode="r") as ws:
                    survey = self.fetch_survey(ws)

                    if survey is None:
                        logger.warning("No survey found in %s, skipping.", sim_file)
                        continue

                    simulated = self.normalized_data(
                        survey.get_entity("Iteration_0_z")[0]
                    )

                    # Create a projection matrix to interpolate simulated data to the observation locations
                    # Assume that lines of simulations are centered at origin
                    if spatial_projection is None:
                        nearest = tree.query(query[:2], k=1)[1]
                        indices = self.get_segment_indices(nearest)
                        spatial_projection = self.spatial_interpolation(
                            indices,
                            survey.vertices,
                            self.params.strike_angles.values[ii],
                        )

                    if time_projection is None:
                        query_times = np.asarray(self.params.survey.channels)
                        simulated_times = np.asarray(survey.channels)

                        # Only interpolate for times within the simulated range
                        time_mask = (query_times > simulated_times.min()) & (
                            query_times < simulated_times.max()
                        )
                        time_projection = self.time_interpolation(
                            query_times[time_mask], simulated_times
                        )
                        observed = observed[time_mask, :]

                    pred = time_projection @ (spatial_projection @ simulated.T).T

                    score = 0.0

                    # if sim_file.stem == "0e50d2da-7ab0-5484-9ffd-365f076cce98":
                    #
                    #     fig, ax = plt.figure(), plt.subplot()

                    # Metric: normalized cross-correlation
                    for obs, pre in zip(observed[:, indices], pred, strict=True):
                        # Full cross-correlation
                        corr = signal.correlate(
                            obs, pre, mode="full"
                        )  # corr[k] ~ sum_t y[t] * x[t - k]
                        # Normalize by energy to get correlation coefficient in [-1, 1]
                        denom = np.linalg.norm(pre) * np.linalg.norm(obs)
                        if denom == 0:
                            corr_norm = np.zeros_like(corr)
                        else:
                            corr_norm = corr / denom

                        score += np.max(corr_norm)
                        # if sim_file.stem == "0e50d2da-7ab0-5484-9ffd-365f076cce98":
                        #     ax.plot(obs , 'r')
                        #     ax.plot(pre, 'k')

                    # if sim_file.stem == "0e50d2da-7ab0-5484-9ffd-365f076cce98":
                    #     plt.show()

                    scores.append(score)
                    files_id.append(sim_file)

            spatial_projection = None
            time_projection = None

            ranked = np.argsort(scores)
            print("Top 3 matches:")
            for rank in ranked[-1:][::-1]:
                print(f"File: {files_id[rank].stem:30s} Score: {scores[rank]:.4f}")
                with Workspace(files_id[rank], mode="r") as ws:
                    survey = self.fetch_survey(ws)
                    ui_json = survey.parent.parent.options
                    ui_json["geoh5"] = ws
                    ifile = InputFile(ui_json=ui_json)
                    options = PlateSimulationOptions.build(ifile)

                    plate = survey.parent.parent.get_entity("plate")[0].copy(
                        parent=self.params.out_group
                    )
                    plate.vertices = plate.vertices + query

                print(f"Best parameters:{options.model.model_dump_json(indent=2)}")


if __name__ == "__main__":
    file = Path(sys.argv[1])
    # file = Path(r"C:\Users\dominiquef\Documents\Workspace\Teck\RnD\plate_match_v2.ui.json")
    PlateMatchDriver.start(file)
