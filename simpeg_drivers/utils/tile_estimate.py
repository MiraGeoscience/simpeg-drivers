# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
import sys
from pathlib import Path
from typing import ClassVar

import matplotlib.pyplot as plt
import numpy as np
from geoapps_utils.driver.data import BaseData
from geoapps_utils.utils.numerical import fibonacci_series, fit_circle
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace, monitored_directory_copy
from scipy.interpolate import interp1d
from tqdm import tqdm

from simpeg_drivers import assets_path
from simpeg_drivers.driver import DRIVER_MAP, InversionDriver
from simpeg_drivers.utils.utils import (
    active_from_xyz,
    simpeg_group_to_driver,
    tile_locations,
)


class TileEstimator:
    def __init__(self, input_file: str | Path | InputFile):
        if isinstance(input_file, str | Path):
            input_file = InputFile.read_ui_json(input_file)

        if not isinstance(input_file, InputFile):
            raise ValueError(
                "Input must be a path to a UI JSON file or an InputFile instance."
            )

        self.params = TileParameters.build(input_file)

    def start(self) -> SimPEGGroup:
        """
        Run the tile estimator.
        """
        driver = simpeg_group_to_driver(self.params.simulation, self.params.geoh5)
        mesh = driver.inversion_mesh.mesh
        locations = driver.inversion_data.locations
        active_cells = active_from_xyz(
            driver.inversion_mesh.entity, locations, method="nearest"
        )
        results = {}
        counts = fibonacci_series(15)[2:]
        for count in tqdm(counts, desc="Estimating tiles:"):
            tiles = tile_locations(
                locations,
                count,
                method="kmeans",
            )
            # Get the median tile
            ind = np.argsort([len(tile) for tile in tiles])[int(count / 2)]
            survey, _, _ = driver.inversion_data.create_survey(
                mesh=mesh, local_index=tiles[ind]
            )
            driver.params.tile_spatial = int(count)
            local_sim, local_map = driver.inversion_data.simulation(
                mesh,
                active_cells,
                survey,
                padding_cells=driver.params.padding_cells,
                tile_id=count,
            )
            results[count] = float(survey.nD) * local_map.shape[0] * count * 8 * 1e-9

        print(f"Computed tile sizes: {results}")

        optimal = self.estimate_optimal_tile(results)

        new_out_group = self.params.simulation.copy(copy_children=False)
        driver.params.tile_spatial = optimal
        driver.params.out_group = new_out_group
        new_out_group.options = driver.params.to_dict(ui_json_format=True)
        new_out_group.metadata = None

        if self.params.out_group is not None:
            new_out_group.parent = self.params.out_group

        if self.params.render_plot:
            figure = self.plot(results, locations, optimal)
            path = self.params.geoh5.h5file.parent / "tile_estimator.png"
            figure.savefig(path)
            new_out_group.add_file(path)
            figure.savefig(path)

        if self.params.monitoring_directory is not None:
            monitored_directory_copy(self.params.monitoring_directory, new_out_group)

        return new_out_group

    @staticmethod
    def estimate_optimal_tile(results: dict) -> int:
        """
        Estimate the optimal number of tiles to use using a circle fit.

        :param results: Dictionary of tile counts and problem sizes.
        """
        tile_counts = np.array(list(results.keys()))
        problem_sizes = np.array(list(results.values()))

        radiis = [np.inf]
        for ind in range(1, len(problem_sizes) - 1):
            size = problem_sizes[ind - 1 : ind + 2]
            counts = tile_counts[ind - 1 : ind + 2]
            rad, _, _ = fit_circle(counts / counts.max(), size / size.max())
            radiis.append(rad[0])

        optimal = tile_counts[np.argmin(radiis)]
        return int(optimal)

    @staticmethod
    def plot(results: dict, locations: np.ndarray, optimal: int):
        """
        Plot the results of the tile estimator.

        :param results: Dictionary of tile counts and problem sizes.
        :param locations: Array of receiver locations.
        :param optimal: Optimal number of tiles.
        """
        tile_counts = np.array(list(results.keys()))
        problem_sizes = np.array(list(results.values()))
        fun = interp1d(tile_counts, problem_sizes)

        figure = plt.figure(figsize=(7.5, 11))
        ax = plt.subplot(2, 1, 1)

        ax.plot(tile_counts, problem_sizes)
        ax.plot(optimal, fun(optimal), "ro")
        ax.set_xlabel("Number of tiles")
        ax.set_aspect(tile_counts.max() / problem_sizes.max())
        ax.set_ylabel("Est. total size (Gb)")

        ax2 = plt.subplot(2, 1, 2)
        tiles = tile_locations(
            locations,
            optimal,
            method="kmeans",
        )
        for tile in tiles:
            ax2.scatter(locations[tile, 0], locations[tile, 1], s=1)

        ax2.set_xlabel("Easting (m)")
        ax2.set_ylabel("Northing (m)")
        ax2.set_aspect("equal")
        plt.show()

        return figure


class TileParameters(BaseData):
    """
    Parameters for the tile estimator.
    """

    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tile_estimator.ui.json"

    simulation: SimPEGGroup
    render_plot: bool = True
    out_group: UIJsonGroup | None = None


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    tile_driver = TileEstimator(file)

    with fetch_active_workspace(tile_driver.params.geoh5, mode="r+"):
        tile_driver.start()
