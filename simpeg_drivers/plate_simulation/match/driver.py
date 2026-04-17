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

import logging
import sys
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Self

import matplotlib.pyplot as plt
import numpy as np
from dask.distributed import Client, Future, progress
from geoapps_utils.base import Driver
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.locations import topo_drape_elevation
from geoapps_utils.utils.logger import get_logger
from geoapps_utils.utils.numerical import inverse_weighted_operator
from geoapps_utils.utils.plotting import symlog
from geoapps_utils.utils.transformations import cartesian_to_polar, rotate_xyz
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.objects import AirborneTEMReceivers, MaxwellPlate, Surface
from geoh5py.objects.maxwell_plate import PlateGeometry
from geoh5py.ui_json import InputFile
from scipy import ndimage, signal
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

from simpeg_drivers.driver import validate_client, validate_workers
from simpeg_drivers.electromagnetics.time_domain.options import CONVERSION
from simpeg_drivers.plate_simulation.match.options import PlateMatchOptions
from simpeg_drivers.plate_simulation.options import ModelOptions, PlateSimulationOptions
from simpeg_drivers.utils.utils import (
    get_default_parallelization_params,
    start_dask_run,
    validate_out_group,
)


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


@contextmanager
def suppress_logging(level=logging.WARNING):
    """
    Temporarily disable logging records at or below the given level.

    :param level: Logging level to suppress (default: logging.WARNING).
    """
    previous_disable_level = logging.root.manager.disable
    logging.disable(level)
    try:
        yield
    finally:
        logging.disable(previous_disable_level)


class PlateMatchDriver(Driver):
    """Sets up and manages workers to run all combinations of swept parameters."""

    _params_class = PlateMatchOptions

    def __init__(
        self,
        params: PlateMatchOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
    ):
        super().__init__(params)

        self._out_group = validate_out_group(self.params)
        self._client: Client | bool = validate_client(client)
        self._workers: list[tuple[str]] = validate_workers(self._client, workers)

        self._drape_heights = self._get_drape_heights()
        self._template = self.get_template()
        self._time_mask, self._time_projection = self.time_mask_and_projection(
            np.asarray(self._template.channels) * CONVERSION[self._template.unit],
            np.asarray(self.params.survey.channels)
            * CONVERSION[self.params.survey.unit],
        )
        self._spatial_tree = cKDTree(self.params.survey.vertices[:, :2])

    @property
    def spatial_tree(self):
        """KDTree for spatial locations of the survey."""
        return self._spatial_tree

    def get_template(self) -> AirborneTEMReceivers:
        """
        Get a template simulation to extract time sampling.
        """
        with Workspace(self.params.simulation_files[0], mode="r") as ws:
            survey = fetch_survey(ws)
            if not isinstance(survey, AirborneTEMReceivers):
                raise GeoAppsError(
                    f"No survey found under Plate Simulation of {self.params.simulation_files[0]}"
                )

            if survey.channels is None:
                raise GeoAppsError(
                    f"No time channels found in survey of {self.params.simulation_files[0]}"
                )

        return survey

    @staticmethod
    def time_mask_and_projection(
        simulated_times, query_times
    ) -> tuple[np.ndarray, csr_matrix]:
        """
        Create a time mask and interpolation matrix from simulation to observation times.

        Assumes that all simulations in the directory have the same time sampling.

        :return: Time mask and time interpolation matrix.
        """
        # Only interpolate for times within the simulated range
        time_mask = (query_times >= simulated_times.min()) & (
            query_times <= simulated_times.max()
        )
        query_times = query_times[time_mask]
        right = np.searchsorted(simulated_times, query_times)
        inds = np.c_[np.maximum(0, right - 1), right].flatten()
        row_ids = np.repeat(np.arange(len(query_times)), 2)

        # Create inverse distance weighting matrix based on time difference
        time_diff = np.abs(query_times[row_ids] - simulated_times[inds])
        time_projection = inverse_weighted_operator(
            time_diff, inds, (len(query_times), len(simulated_times)), 1.0, 1e-12
        )
        return time_mask, time_projection

    def spatial_mask_and_projection(
        self, location: np.ndarray, strike_angle: float
    ) -> tuple[np.ndarray, csr_matrix]:
        """
        Create a spatial mask and interpolation matrix from simulation to observation locations.

        :param location: Query location (x, y, z).
        :param strike_angle: Strike angle with respect to the plate orientation.

        :return: Spatial mask and spatial interpolation matrix.
        """
        nearest = self.spatial_tree.query(location[:2], k=1)[1]
        indices = self.params.survey.get_segment_indices(
            nearest, self.params.max_distance
        )
        spatial_projection = self.spatial_interpolation(
            indices,
            np.abs(strike_angle),
        )
        return indices, spatial_projection

    def simpeg_run(self):
        """
        Run call to simpeg.
        """

    def start_message(self):
        """
        Starting message displayed by the logger.
        """

    @classmethod
    def start(cls, filepath: str | Path, mode="r+", **_) -> Self:
        """Start the parameter matching from a ui.json file."""
        logger.info("Loading input file . . .")
        filepath = Path(filepath).resolve()

        # TODO: Replace with UIJson when fully implemented
        # uijson = PlateMatchUIJson.read(filepath)
        uijson = InputFile.read_ui_json(filepath)

        with uijson.geoh5.open(mode=mode):
            try:
                options = PlateMatchOptions.build(uijson)
                logger.info("Initializing application . . .")
                driver = cls(options)
                logger.info("Running application . . .")
                driver.run()
                logger.info("Results saved to %s", options.geoh5.h5file)

            except GeoAppsError as error:
                logger.warning("\n\nApplicationError: %s\n\n", error)
                sys.exit(1)

        return driver

    def _create_plate_from_parameters(
        self, index_center: int, model_options: ModelOptions, strike_angle: float
    ) -> MaxwellPlate:
        """
        Create a MaxwellPlate object from the parameters of the survey and model options
        at the location of the query point.

        :param index_center: Index of the center point in the survey vertices.
        :param model_options: Model options containing plate geometry parameters.
        :param strike_angle: Strike angle to correct the plate orientation.

        :return: MaxwellPlate object created from the parameters.
        """
        center = self.params.survey.vertices[index_center]
        center[2] = (
            self._drape_heights[index_center]
            - model_options.overburden_options.thickness
        )
        indices = self.params.survey.get_segment_indices(
            index_center, self.params.max_distance
        )
        segment = self.params.survey.vertices[indices]
        delta = np.median(np.diff(segment, axis=0), axis=0)
        azimuth = 90 - np.rad2deg(np.arctan2(delta[1], delta[0]))

        plate_geometry = PlateGeometry.model_validate(
            {
                "position": {
                    "x": center[0],
                    "y": center[1],
                    "z": center[2],
                },
                "width": model_options.plate_options.geometry.dip_length,
                "thickness": model_options.plate_options.geometry.width,
                "length": model_options.plate_options.geometry.strike_length,
                "dip": model_options.plate_options.geometry.dip,
                "dip_direction": (azimuth + strike_angle) % 360,
            }
        )
        plate = MaxwellPlate.create(
            self.params.geoh5, geometry=plate_geometry, parent=self.out_group
        )
        plate.metadata = model_options.model_dump()

        return plate

    def _get_drape_heights(self) -> np.ndarray:
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

    @staticmethod
    def plot_figure(
        locations, survey, observed, time_projection, spatial_projection, center: int
    ) -> BytesIO:
        """
        Generate a figure showing the observed and simulated plate locations.

        :param locations: Array of locations.
        :param survey: Survey object.
        :param observed: Array of observed data.
        :param time_projection: Array performing the time interpolation.
        :param spatial_projection: Array performing the spatial interpolation.
        :param center: Index of the center point in the survey vertices.

        :return: BytesIO object containing the figure.
        """
        distances = np.linalg.norm(locations[0, :] - locations, axis=1)
        horizontal_shift = (distances - np.mean(distances))[center]

        in_early_val = np.min(np.abs(observed[0, :]))
        data = normalized_data(observed, threshold=in_early_val)
        preds = get_normalized_predicted(
            survey, spatial_projection, time_projection, in_early_val
        )

        preds *= data.max() / preds.max()

        fig, ax = plt.figure(figsize=(12, 10)), plt.subplot()
        for obs, pred in zip(data, preds, strict=True):
            ax.plot(distances, obs, c="0.75", lw=2)
            ax.plot(distances + horizontal_shift, pred, c="k", ls="--", lw=2)

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Log Normalized Amplitude")
        ax.legend(["Observed", "Simulated"])

        buf = BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        return buf

    def spatial_interpolation(
        self,
        indices: np.ndarray,
        strike_angle: float | None = None,
    ) -> csr_matrix:
        """
        Create a spatial interpolation matrix from simulation to observation locations.

        :param indices: Indices for the line segment of the observation locations.
        :param strike_angle: Optional strike angle to correct azimuths.

        :return: Spatial interpolation matrix.
        """
        # Compute local coordinates for the current line segment
        delta = (
            self.params.survey.vertices[indices]
            - self.params.survey.vertices[indices[0], :]
        )
        azimuths = np.mean(np.rad2deg(np.arctan2(delta[:, 1], delta[:, 0]))[1:])
        azimuths -= np.abs(strike_angle) if strike_angle else 0.0

        # Assume simulations are West to East
        arg_center = int(np.median(indices))
        local_xyz = (
            self.params.survey.vertices[indices]
            - self.params.survey.vertices[arg_center, :]
        )
        local_xyz[:, 2] = (
            self.params.survey.vertices[indices, 2] - self._drape_heights[indices]
        )
        local_xyz = rotate_xyz(local_xyz, [0, 0, 0], -azimuths)

        # Get polar coordinates
        local_polar = cartesian_to_polar(local_xyz)
        local_polar[local_polar[:, 1] > 180, 0] *= -1
        local_polar[local_polar[:, 1] > 180, 1] -= 180
        # Transform azimuth to arc-lengths
        local_polar[:, 1] = np.abs(
            local_polar[:, 0] * np.deg2rad(90 - local_polar[:, 1])
        )

        # Get template polar coordinates
        sim_polar = cartesian_to_polar(self._template.vertices)
        sim_polar[sim_polar[:, 1] > 180, 0] *= -1
        sim_polar[sim_polar[:, 1] > 180, 1] -= 180
        sim_polar[:, 1] = np.abs(sim_polar[:, 0] * np.deg2rad(90 - sim_polar[:, 1]))

        sim_tree = cKDTree(sim_polar)
        rad, inds = sim_tree.query(local_polar, k=14)
        inds = np.minimum(self._template.vertices.shape[0] - 1, inds)

        return inverse_weighted_operator(
            rad.flatten(),
            inds.flatten(),
            (local_xyz.shape[0], self._template.vertices.shape[0]),
            1.0,
            1e-1,
        )

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""
        logger.info(
            "Running %s . . .",
            self.params.title,
        )
        observed = get_data_array(self.params.data)[self._time_mask, :]
        strike_angle = (
            np.zeros(self.params.queries.n_vertices)
            if self.params.strike_angles is None
            else self.params.strike_angles.values
        )
        names = []
        results = []
        for ii, query in enumerate(self.params.queries.vertices):
            # Find the nearest survey location to the query point
            indices, spatial_projection = self.spatial_mask_and_projection(
                query, strike_angle[ii]
            )
            flip = is_up_dip(observed[:, indices])
            # Loop through files and compute scores and find the best match
            scores, centers = self.run_scores(spatial_projection, observed[:, indices])
            ranked = np.argsort(scores)
            best = ranked[0]
            logger.info(
                "File: %s \nScore: %.4f",
                self.params.simulation_files[best].name,
                scores[best],
            )
            with Workspace(self.params.simulation_files[best], mode="r") as ws:
                survey = fetch_survey(ws)

                ui_json = survey.parent.parent.options

                ui_json["geoh5"] = ws
                ifile = InputFile(ui_json=ui_json)

                with suppress_logging():
                    options = PlateSimulationOptions.build(ifile)

                dir_correction = strike_angle[ii] + 180 if flip else strike_angle[ii]
                ind_center = int(centers[best])
                plate = self._create_plate_from_parameters(
                    int(indices[ind_center]), options.model, dir_correction
                )
                plate.name = f"Query [{ii}]"
                figure = self.plot_figure(
                    self.params.survey.vertices[indices, :2],
                    survey,
                    observed[:, indices],
                    self._time_projection,
                    spatial_projection,
                    ind_center,
                )
                plate.add_file(figure.getvalue(), name=f"profile_{plate.name}.png")

            names.append(self.params.simulation_files[best].name)
            results.append(scores[best])

        out = self.params.queries.copy(parent=self.out_group)
        out.add_data(
            {
                "file": {
                    "values": np.array(names, dtype="U"),
                    "primitive_type": "TEXT",
                },
                "score": {
                    "values": np.array(results),
                },
            }
        )

        return out

    def run_scores(self, spatial_projection, data) -> tuple[np.ndarray, np.ndarray]:
        """
        Run the scoring function for all simulation files in parallel using Dask.

        :param spatial_projection: Spatial interpolation matrix for the current query.
        :param data: Prepared observed data for the current query.

        :return: Tuple of scores and corresponding center indices for each simulation file.
        """
        file_split = np.array_split(
            self.params.simulation_files, np.maximum(1, len(self._workers) * 10)
        )
        tasks = []
        for file_batch in file_split:
            args = (
                file_batch,
                spatial_projection,
                self._time_projection,
                data,
            )

            tasks.append(
                self._client.submit(batch_files_score, *args)
                if self._client
                else batch_files_score(*args)
            )

        # Display progress bar
        if isinstance(tasks[0], Future):
            progress(tasks)
            tasks = self._client.gather(tasks)

        scores, centers = np.vstack(tasks).T

        return scores, centers

    @classmethod
    def start_dask_run(
        cls, json_path: Path, n_workers: int | None = None, n_threads: int | None = None
    ):
        """
        Runs plate matching application with Dask optimization.

        :param json_path: Path to input file (.ui.json) for the application.
        :param n_workers: Number of workers to use.
        :param n_threads: Number of threads to use.
        """
        start_dask_run(cls, json_path, n_workers=n_workers, n_threads=n_threads)


def is_up_dip(data: np.ndarray) -> bool:
    """
    Prepare data for scoring by checking for multiple channels and normalizing.

    param data: Array of data channels per location.

    :return: Tuple of prepared data array, whether locations were reversed.
    """
    data_array = normalized_data(data)

    # Guess what the down-dip direction is based on integral
    centered = data_array - np.min(data_array, axis=1)[:, None]
    mid = centered.shape[1] // 2
    left = np.sum(centered[:, :mid], axis=1)
    right = np.sum(centered[:, mid:], axis=1)

    # Mostly on the left suggests the peaks are migrating up-dip and should be reversed
    if np.mean(left > right) > 0.5:
        return True

    return False


def get_data_array(property_group: PropertyGroup) -> np.ndarray:
    """
    Extract data array from a property group.

    :param property_group: Property group containing data values.

    :return: Data array with shape (n_times, n_locations).
    """
    table = property_group.table()
    return np.vstack(table.tolist()).T


def normalized_data(
    data: np.ndarray, scale: float = 1, threshold: float | None = None
) -> np.ndarray:
    """
    Return data from a property group with symlog, zero median and unit max normalization.

    :param data: Array of data channels per location.
    :param threshold: Percentile threshold for symlog normalization.

    :return: Normalized data array.
    """
    scales_data = data * scale

    if threshold is None:
        threshold = np.percentile(scales_data, 5)

    log_data = symlog(scales_data, threshold)

    return log_data


def fetch_survey(workspace: Workspace) -> AirborneTEMReceivers | None:
    """Fetch the survey from the workspace."""
    for group in workspace.groups:
        if isinstance(group, SimPEGGroup):
            for child in group.children:
                if isinstance(child, AirborneTEMReceivers):
                    return child

    return None


def get_normalized_predicted(
    survey: AirborneTEMReceivers, spatial_projection, time_projection, threshold
) -> np.ndarray:
    """
    From a survey entity, retrieve the predicted data group,
    interpolate and normalize the data

    :param survey: AirborneTEMReceivers entity
    :param spatial_projection: Spatial interpolation matrix for the current query.
    :param time_projection: Time interpolation matrix for the current query.
    :param threshold: Percentile threshold for symlog normalization.

    :return: Normalized predicted data
    """
    data_entity = survey.get_entity("Iteration_0_vertical")[0]

    if data_entity is None:
        data_entity = survey.get_entity("Iteration_0_z")[0]

    simulated = get_data_array(data_entity)

    pred = time_projection @ (spatial_projection @ simulated.T).T
    scale = threshold / np.min(np.abs(pred[0, :]))
    pred = normalized_data(pred, scale=scale, threshold=threshold)

    # Smooth out the spatial interpolation
    pred = ndimage.convolve1d(pred, np.ones(4) / 4, axis=1)

    return pred


def batch_files_score(
    files: Path | list[Path], spatial_projection, time_projection, observed
) -> list[tuple[float, int]]:
    """
    Process a batch of simulation files and compute scores against observed data.

    Attempt to find the best collocation of the simulated and observed data by
    finding the median index of the maximum correlation across channels.

    :param files: Simulation file or list of simulation files to process.
    :param spatial_projection: Spatial interpolation matrix.
    :param time_projection: Time interpolation matrix.
    :param observed: Normalized (symlog) observed data array.

    :return: List of scores for each simulation file.
    """
    scores = []

    if isinstance(files, Path):
        files = [files]

    in_early_val = np.minimum(np.abs(observed[0, :]), 1e-20)
    data = normalized_data(observed, threshold=in_early_val)

    for sim_file in files:
        with Workspace(sim_file, mode="r") as ws:
            survey = fetch_survey(ws)

            if survey is None:
                logger.warning("No survey found in %s, skipping.", sim_file)
                continue

            pred = get_normalized_predicted(
                survey, spatial_projection, time_projection, in_early_val
            )
            score = 0.0
            indices = []
            # Metric: normalized cross-correlation
            for obs, pre in zip(data, pred, strict=True):
                # Full cross-correlation
                corr = signal.correlate(obs, pre, mode="same")
                # Normalize by energy to get correlation coefficient in [-1, 1]
                denom = np.linalg.norm(pre) * np.linalg.norm(obs)
                if denom == 0:
                    corr_norm = np.zeros_like(corr)
                else:
                    corr_norm = corr / denom

                score += np.linalg.norm(obs - pre) / np.linalg.norm(obs)
                indices.append(np.argmax(corr_norm))

            scores.append((score, np.median(indices)))

    return scores


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    n_w, n_t = get_default_parallelization_params(file)

    PlateMatchDriver.start_dask_run(file, n_workers=n_w, n_threads=n_t)
