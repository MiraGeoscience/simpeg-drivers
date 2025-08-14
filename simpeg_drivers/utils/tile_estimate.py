# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
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
import logging
import sys
from pathlib import Path
from typing import ClassVar

import matplotlib.pyplot as plt
import numpy as np
from discretize import TreeMesh
from geoapps_utils.driver.data import BaseData
from geoapps_utils.driver.driver import BaseDriver
from geoapps_utils.utils.numerical import fibonacci_series, fit_circle
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from scipy.interpolate import interp1d
from tqdm import tqdm

from simpeg_drivers import assets_path
from simpeg_drivers.components.factories.misfit_factory import MisfitFactory
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.utils import (
    active_from_xyz,
    simpeg_group_to_driver,
    tile_locations,
)


logger = logging.getLogger(__name__)


class TileParameters(BaseData):
    """
    Parameters for the tile estimator.
    """

    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tile_estimator.ui.json"

    simulation: SimPEGGroup
    render_plot: bool = True
    out_group: UIJsonGroup | None = None


class TileEstimator(BaseDriver):
    """
    Class to estimate the optimal number of tiles for a given mesh and receiver locations.

    The driver loops over a range of tile counts and estimates the total problem size
    for each count. The optimal number of tiles is estimated from the point
    of maximum curvature using a circle fit. This assumes a point of
    diminishing returns in terms of problem size and the overall cost of
    creating more tiles.
    """

    _params_class = TileParameters

    def __init__(self, params: TileParameters):
        self._driver: InversionDriver | None = None
        self._mesh: TreeMesh | None = None
        self._locations: np.ndarray | None = None
        self._active_cells: np.ndarray | None = None

        super().__init__(params)

    def get_results(self, max_tiles: int = 13) -> dict:
        """
        Run the tile estimator over a Fibonacci series up to
        the maximum number of tiles.
        """
        results = {}
        counts = fibonacci_series(max_tiles)[2:].tolist()

        if counts[-1] < max_tiles:
            counts.append(max_tiles)

        for count in tqdm(counts, desc="Estimating tiles:"):
            if count > len(self.locations):
                break

            tiles = tile_locations(
                self.locations,
                count,
                method="kmeans",
            )
            # Get the median tile
            ind = int(np.argsort([len(tile) for tile in tiles])[int(count / 2)])
            self.driver.params.tile_spatial = int(count)
            sim, _, _, mapping = MisfitFactory.create_nested_simulation(
                self.driver.inversion_data,
                self.driver.inversion_mesh,
                None,
                self.active_cells,
                tiles[ind],
                tile_id=ind,
                padding_cells=self.driver.params.padding_cells,
            )

            # Estimate total size in Gb
            results[count] = float(sim.survey.nD) * mapping.shape[0] * count * 8 * 1e-9

        return results

    def run(self) -> SimPEGGroup:
        """
        Run the tile estimator.
        """
        # TODO find out why this is needed. Without I get an error because the
        # data_object is no longer the parent of tmi_channel.
        _ = self.driver.inversion  # Triggers creation of something
        results = self.get_results()

        logger.info(
            "Estimates:\n%s\n%s",
            "Tiling \t Total size (Gb) ",
            "\n".join(f"{key} \t {value:.2e}" for key, value in results.items()),
        )

        optimal = self.estimate_optimal_tile(results)
        out_group = self.generate_optimal_group(optimal)

        logger.info("Optimal number of tile(s): %i", optimal)

        if self.params.out_group is not None:
            out_group = self.params.out_group

        if self.params.render_plot:
            fig_name = "tile_estimator.png"
            logger.info("Saving figure '%s' to disk and to geoh5.", fig_name)
            path = self.params.geoh5.h5file.parent / fig_name
            figure = self.plot(results, self.locations, optimal)
            figure.savefig(path)
            out_group.add_file(path)

        self.update_monitoring_directory(out_group)

        return out_group

    @property
    def driver(self) -> InversionDriver:
        """
        Return the driver instance.
        """
        if self._driver is None:
            self._driver = simpeg_group_to_driver(
                self.params.simulation, self.params.geoh5
            )

        return self._driver

    @property
    def mesh(self) -> TreeMesh:
        """
        The input Octree mesh.
        """
        if self._mesh is None:
            self._mesh = self.driver.inversion_mesh.mesh
        return self._mesh

    @property
    def locations(self) -> np.ndarray:
        """
        All receiver locations.
        """
        if self._locations is None:
            self._locations = self.driver.inversion_data.locations

        return self._locations

    @property
    def active_cells(self) -> np.ndarray:
        """
        Active cells in the mesh.
        """
        if self._active_cells is None:
            self._active_cells = active_from_xyz(
                self.driver.inversion_mesh.entity, self.locations, method="nearest"
            )
        return self._active_cells

    @staticmethod
    def estimate_optimal_tile(results: dict[int, int]) -> int:
        """
        Estimate the optimal number of tiles to use using a circle fit.

        :param results: Dictionary of tile counts and problem sizes.
        """
        tile_counts = np.array(list(results.keys()))
        problem_sizes = np.array(list(results.values()))

        radiis = [np.inf]
        for ind in range(1, len(problem_sizes) - 1):
            size = problem_sizes[ind - 1 : ind + 2].copy()
            counts = tile_counts[ind - 1 : ind + 2].astype(float)
            rad, x0, y0 = fit_circle(counts, size)
            radiis.append(rad[0])

        optimal = tile_counts[np.argmin(radiis)]
        return int(optimal)

    def generate_optimal_group(self, optimal: int):
        """
        Generate a new SimPEGGroup with the optimal number of tiles.
        """
        out_group = self.params.simulation.copy(copy_children=False)
        self.driver.params.tile_spatial = optimal
        self.driver.params.out_group = out_group
        out_group.options = self.driver.params.serialize()
        out_group.metadata = None

        if self.params.out_group is not None:
            out_group.parent = self.params.out_group

        return out_group

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

        return figure


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    TileEstimator.start(file)
