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

import multiprocessing
import sys
from pathlib import Path

import numpy as np
from dask.distributed import Future, progress
from geoapps_utils.run import load_ui_json_as_dict
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
from scipy import signal
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree
from typing_extensions import Self

from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.plate_simulation.match.options import PlateMatchOptions
from simpeg_drivers.plate_simulation.options import ModelOptions, PlateSimulationOptions


logger = get_logger(name=__name__, level_name=False, propagate=False, add_name=False)


class PlateMatchDriver(BaseDriver):
    """Sets up and manages workers to run all combinations of swept parameters."""

    _params_class = PlateMatchOptions

    def __init__(
        self, params: PlateMatchOptions, workers: list[tuple[str]] | None = None
    ):
        super().__init__(params, workers=workers)

        self._drape_heights = self._get_drape_heights()
        self._template = self.get_template()
        self._time_mask, self._time_projection = self.time_mask_and_projection()

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

    def time_mask_and_projection(self) -> tuple[np.ndarray, csr_matrix]:
        """
        Create a time mask and interpolation matrix from simulation to observation times.

        Assumes that all simulations in the directory have the same time sampling.

        :return: Time mask and time interpolation matrix.
        """
        simulated_times = np.asarray(self._template.channels)
        query_times = np.asarray(self.params.survey.channels)
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
        center = self.params.survey.vertices[index_center]
        center[2] = (
            self._drape_heights[index_center] - model_options.overburden_model.thickness
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
                "width": model_options.plate_model.dip_length,
                "thickness": model_options.plate_model.width,
                "length": model_options.plate_model.strike_length,
                "dip": model_options.plate_model.dip,
                "dip_direction": (azimuth + strike_angle) % 360,
            }
        )
        plate = MaxwellPlate.create(
            self.params.geoh5, geometry=plate_geometry, parent=self.params.out_group
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
        local_polar = cartesian_to_polar(
            self.params.survey.vertices[indices],
            origin=np.r_[self.params.survey.vertices[indices, :2].mean(axis=0), 0],
        )
        local_polar[local_polar[:, 1] >= 180, 0] *= -1  # Wrap azimuths

        # Flip the line segment if the azimuth angle suggests the opposite direction
        start_line = len(indices) // 2
        if np.median(local_polar[:start_line, 1]) < 180:
            local_polar = local_polar[::-1, :]

        local_polar[:, 1] = (
            0.0 if strike_angle is None else strike_angle
        )  # Align azimuths to zero

        # Convert to polar coordinates (distance, azimuth, height)
        query_polar = cartesian_to_polar(self._template.vertices)
        query_polar[query_polar[:, 1] >= 180, 0] *= -1
        query_polar[:, 1] = query_polar[:, 1] % 180  # Wrap azimuths

        # Get the 8 nearest neighbors in the simulation to each observation point
        sim_tree = cKDTree(query_polar)
        rad, inds = sim_tree.query(local_polar, k=8)
        inds = np.minimum(query_polar.shape[0] - 1, inds)
        return inverse_weighted_operator(
            rad.flatten(),
            inds.flatten(),
            (local_polar.shape[0], self._template.vertices.shape[0]),
            2.0,
            1e-1,
        )

    def run(self):
        """Loop over all trials and run a worker for each unique parameter set."""
        logger.info(
            "Running %s . . .",
            self.params.title,
        )
        observed = get_data_array(self.params.data)[self._time_mask, :]
        tree = cKDTree(self.params.survey.vertices[:, :2])
        file_split = np.array_split(
            self.params.simulation_files, np.maximum(1, len(self.workers) * 10)
        )
        names = []
        results = []
        for ii, query in enumerate(self.params.queries.vertices):
            # Find the nearest survey location to the query point
            nearest = tree.query(query[:2], k=1)[1]
            indices = self.params.survey.get_segment_indices(
                nearest, self.params.max_distance
            )
            strike_angle = (
                0
                if self.params.strike_angles is None
                else self.params.strike_angles.values[ii]
            )
            data, flip = prepare_data(observed[:, indices])

            spatial_projection = self.spatial_interpolation(
                indices,
                np.abs(strike_angle),
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
                    self.client.submit(batch_files_score, *args)
                    if self.client
                    else batch_files_score(*args)
                )

            # Display progress bar
            if isinstance(tasks[0], Future):
                progress(tasks)
                tasks = self.client.gather(tasks)

            scores, centers = np.vstack(tasks).T
            ranked = np.argsort(scores)
            best = ranked[0]
            # TODO: Return top N matches
            # for rank in ranked[-1:][::-1]:
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
                options = PlateSimulationOptions.build(ifile)

                dir_correction = strike_angle + 180 if flip else strike_angle

                plate = self._create_plate_from_parameters(
                    int(indices[int(centers[best])]), options.model, dir_correction
                )
                plate.name = f"Query [{ii}]"

            names.append(self.params.simulation_files[best].name)
            results.append(scores[best])

        out = self.params.queries.copy(parent=self.params.out_group)
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

    @classmethod
    def start_dask_run(
        cls,
        json_path: Path,
        n_workers: int | None = None,
        n_threads: int | None = None,
        save_report: bool = True,
    ):
        """Overload configurations of BaseDriver Dask config settings."""
        # Force distributed on 1D problems
        if n_workers is None:
            cpu_count = multiprocessing.cpu_count()

            if cpu_count < 16:
                n_threads = n_threads or 2
            else:
                n_threads = n_threads or 4

            n_workers = cpu_count // n_threads

        super().start_dask_run(
            json_path, n_workers=n_workers, n_threads=n_threads, save_report=save_report
        )


def prepare_data(data: np.ndarray) -> tuple[np.ndarray, bool]:
    """
    Prepare data for scoring by checking for multiple channels and normalizing.

    param data_array: Array of data channels per location.

    :return: Tuple of prepared data array, whether locations were reversed.
    """
    data_array = normalized_data(data)

    # Guess what the down-dip direction is based on migration of peaks
    max_ind = np.argmax(data_array, axis=1)

    # Check if peaks migrate in a consistent direction across channels
    diffs = np.diff(max_ind)
    if np.median(diffs) < 0:
        return data_array[:, ::-1], True  # Reverse channels if peaks migrate up-dip

    return data_array, False


def get_data_array(property_group: PropertyGroup) -> np.ndarray:
    """Extract data array from a property group."""
    table = property_group.table()
    return np.vstack([table[name] for name in table.dtype.names])


def normalized_data(data: np.ndarray, threshold=5) -> np.ndarray:
    """
    Return data from a property group with symlog, zero mean and unit max normalization.

    :param data: Array of data channels per location.
    :param threshold: Percentile threshold for symlog normalization.

    :return: Normalized data array.
    """
    thresh = np.percentile(np.abs(data), threshold)
    log_data = symlog(data, thresh)
    centered_log = log_data - np.mean(log_data)
    return centered_log / np.abs(centered_log).max()


def fetch_survey(workspace: Workspace) -> AirborneTEMReceivers | None:
    """Fetch the survey from the workspace."""
    for group in workspace.groups:
        if isinstance(group, SimPEGGroup):
            for child in group.children:
                if isinstance(child, AirborneTEMReceivers):
                    return child

    return None


def batch_files_score(
    files: Path | list[Path], spatial_projection, time_projection, observed
) -> list[tuple[float, int]]:
    """
    Process a batch of simulation files and compute scores against observed data.

    :param files: Simulation file or list of simulation files to process.
    :param spatial_projection: Spatial interpolation matrix.
    :param time_projection: Time interpolation matrix.
    :param observed: Observed data array.

    :return: List of scores for each simulation file.
    """
    scores = []

    if isinstance(files, Path):
        files = [files]

    for sim_file in files:
        with Workspace(sim_file, mode="r") as ws:
            survey = fetch_survey(ws)

            if survey is None:
                logger.warning("No survey found in %s, skipping.", sim_file)
                continue

            simulated = get_data_array(survey.get_entity("Iteration_0_z")[0])
            pred = time_projection @ (spatial_projection @ simulated.T).T
            pred = normalized_data(pred)
            score = 0.0
            indices = []
            # Metric: normalized cross-correlation
            for obs, pre in zip(observed, pred, strict=True):
                # Scale pre on obs
                vals = pre / np.abs(pre).max() * np.abs(obs).max()

                # Full cross-correlation
                corr = signal.correlate(obs, vals, mode="same")
                # Normalize by energy to get correlation coefficient in [-1, 1]
                denom = np.linalg.norm(vals) * np.linalg.norm(obs)
                if denom == 0:
                    corr_norm = np.zeros_like(corr)
                else:
                    corr_norm = corr / denom

                score += np.linalg.norm(obs - vals)
                indices.append(np.argmax(corr_norm))

            scores.append((score, np.median(indices)))

    return scores


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    input_file = load_ui_json_as_dict(file)
    PlateMatchDriver.start_dask_run(
        file,
        n_workers=input_file.get("n_workers", None),
        n_threads=input_file.get("n_threads", None),
        save_report=input_file.get("performance_report", False),
    )
