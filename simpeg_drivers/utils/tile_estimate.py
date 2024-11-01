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
from copy import deepcopy
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from geoapps_utils.driver.data import BaseData
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace, monitored_directory_copy
from scipy.interpolate import interp1d
from tqdm import tqdm

from simpeg_drivers.driver import DRIVER_MAP, InversionDriver
from simpeg_drivers.utils.utils import (
    active_from_xyz,
    fibonacci_series,
    fit_circle,
    tile_locations,
)


class TileEstimator:
    def __init__(self, filepath: str | Path):
        ifile = InputFile.read_ui_json(filepath)
        self.params = TileParameters.build(ifile)

        driver_dict = deepcopy(self.params.simulation.options)
        driver_dict["geoh5"] = self.params.geoh5
        self.driver_inputs = InputFile(ui_json=driver_dict)
        inversion_type = self.driver_inputs.ui_json["inversion_type"]

        mod_name, class_name = DRIVER_MAP.get(inversion_type)
        module = __import__(mod_name, fromlist=[class_name])
        self.driver_class: type[InversionDriver] = getattr(module, class_name)

    def start(self):
        """
        Run the tile estimator.
        """
        driver_params = self.driver_class._params_class.build(self.driver_inputs)  # pylint: disable=protected-access
        driver = self.driver_class(driver_params)
        mesh = driver.inversion_mesh.mesh
        locations = driver.inversion_data.locations
        active_cells = active_from_xyz(
            driver.inversion_mesh.entity, locations, method="nearest"
        )
        results = {}
        counts = fibonacci_series(10)[2:]
        for count in tqdm(counts, desc="Estimating tiles:"):
            tiles = tile_locations(
                locations,
                count,
                method="kmeans",
            )
            # Get the largest tile
            ind = np.argsort([len(tile) for tile in tiles])[-1]
            survey, _, _ = driver.inversion_data.create_survey(
                mesh=mesh, local_index=tiles[ind]
            )
            local_sim, local_map = driver.inversion_data.simulation(
                mesh,
                active_cells,
                survey,
                padding_cells=driver_params.padding_cells,
                tile_id=count,
            )
            results[count] = float(survey.nD) * local_map.shape[0] * count * 8 * 1e-9

        print(f"Computed tile sizes: {results}")

        optimal = self.estimate_optimal_tile(results)

        new_out_group = self.params.simulation.copy(copy_children=False)
        driver_params.tile_spatial = optimal
        driver_params.out_group = new_out_group
        new_out_group.options = driver_params.to_dict(ui_json_format=True)
        new_out_group.metadata = None

        if self.params.out_group is not None:
            new_out_group.parent = self.params.out_group

        if self.params.render_plot:
            figure = self.plot(results, locations, optimal)
            path = self.params.geoh5.h5file.parent / "tile_estimator.png"
            new_out_group.add_file(path)
            figure.savefig(path)

        if self.params.monitoring_directory is not None:
            monitored_directory_copy(self.params.monitoring_directory, new_out_group)

    @staticmethod
    def estimate_optimal_tile(results) -> int:
        """
        Estimate the optimal number of tiles to use using a circle fit.
        """
        tile_counts = np.array(list(results.keys()))
        problem_sizes = np.array(list(results.values()))
        rad, x0, y0 = fit_circle(
            tile_counts / tile_counts.max(), problem_sizes / problem_sizes.max()
        )
        axis = np.r_[x0, y0]
        axis /= np.linalg.norm(axis)

        optimal = np.max([1, int((x0 - axis[0] * rad)[0] * tile_counts.max())])
        return int(optimal)

    @staticmethod
    def plot(results: dict, locations: np.ndarray, optimal: int):
        """
        Plot the results of the tile estimator.
        """
        tile_counts = np.array(list(results.keys()))
        problem_sizes = np.array(list(results.values()))
        fun = interp1d(tile_counts, problem_sizes)

        figure = plt.figure(figsize=(12, 10))
        ax = plt.subplot(2, 1, 1)

        ax.plot(tile_counts, problem_sizes)
        ax.plot(optimal, fun(optimal), "ro")
        ax.set_xlabel("Number of tiles")
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
        ax2.set_title(f"Data distribution for {optimal} tiles")
        ax2.set_aspect("equal")
        plt.show()

        return figure


class TileParameters(BaseData):
    """
    Parameters for the tile estimator.
    """

    simulation: SimPEGGroup
    render_plot: bool = True
    out_group: UIJsonGroup | None = None


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    # file = Path(r"C:\Users\dominiquef\Desktop\Tests\tile_estimator.ui.json")
    tile_driver = TileEstimator(file)

    with fetch_active_workspace(tile_driver.params.geoh5, mode="r+"):
        tile_driver.start()
