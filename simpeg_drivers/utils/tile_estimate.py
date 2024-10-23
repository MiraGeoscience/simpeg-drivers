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

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from geoapps_utils.driver.data import BaseData
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace, monitored_directory_copy
from scipy.interpolate import interp1d
from tqdm import tqdm

from simpeg_drivers.driver import DRIVER_MAP
from simpeg_drivers.utils.utils import active_from_xyz, tile_locations


def fit_sphere(x_val: np.ndarray, y_val) -> tuple:
    """
    Compute the least-square sphere fit to a set of points.

    :param x_val: x-coordinates of the points
    :param y_val: y-coordinates of the points

    :return: radius, x0, y0
    """
    # Build linear system
    A = np.c_[x_val * 2, y_val * 2, np.ones_like(x_val)]

    # Right-hand side
    f = np.zeros((len(x_val), 1))
    f[:, 0] = (x_val * x_val) + (y_val * y_val)

    # Find the least-square solution
    coef, _, _, _ = np.linalg.lstsq(A, f, rcond=None)

    # Compute radius
    radius = (coef[0] ** 2.0 + coef[1] ** 2.0 + coef[2]) ** 0.5

    return radius, coef[0], coef[1]


def tile_estimator(file_path: Path):
    """
    Estimate the number of tiles required to process a large file.
    """
    ifile = InputFile.read_ui_json(file_path)
    params = parameters.build(ifile)

    driver_dict = params.simulation.options
    driver_dict["geoh5"] = params.geoh5

    with fetch_active_workspace(params.geoh5, mode="r+"):
        driver_inputs = InputFile(ui_json=driver_dict)
        inversion_type = driver_inputs.data["inversion_type"]

        mod_name, class_name = DRIVER_MAP.get(inversion_type)
        module = __import__(mod_name, fromlist=[class_name])
        driver_class = getattr(module, class_name)

        print("Initializing base driver application . . .")

        driver_params = driver_class._params_class.build(driver_inputs)
        driver = driver_class(driver_params)
        mesh = driver.inversion_mesh.mesh
        locations = driver.inversion_data.locations
        active_cells = active_from_xyz(
            driver.inversion_mesh.entity, locations, method="nearest"
        )
        problem_sizes = []
        tile_counts = []
        fob_1, fob_2 = 0, 1
        for _ in tqdm(range(8), desc="Estimating tiles:"):
            count = fob_1 + fob_2

            if count > len(locations):
                break

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
            local_sim, local_map = driver.inversion_data.simulation(
                mesh,
                active_cells,
                survey,
                padding_cells=driver_params.padding_cells,
                tile_id=count,
            )
            problem_sizes.append(
                float(survey.nD) * local_map.shape[0] * count * 8 * 1e-9
            )
            tile_counts.append(count)
            fob_1, fob_2 = fob_2, count

        tile_counts = np.array(tile_counts)
        problem_sizes = np.array(problem_sizes)
        fun = interp1d(tile_counts, problem_sizes)

        figure = plt.figure(figsize=(12, 10))
        ax = plt.subplot(2, 1, 1)

        rad, x0, y0 = fit_sphere(
            tile_counts / tile_counts.max(), problem_sizes / problem_sizes.max()
        )
        axis = np.r_[x0, y0]
        axis /= np.linalg.norm(axis)

        optimal = int((x0 - axis[0] * rad)[0] * tile_counts.max())
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

        figure.savefig(file_path.parent / "tile_estimator.png")

        new_out_group = driver.out_group.copy(copy_children=False)
        driver_params.tile_spatial = count
        driver_params.out_group = new_out_group
        new_out_group.options = driver_params.to_dict(ui_json_format=True)
        new_out_group.add_file(file_path.parent / "tile_estimator.png")

        if params.monitoring_directory is not None:
            monitored_directory_copy(params.monitoring_directory, new_out_group)


class parameters(BaseData):
    """
    Parameters for the tile estimator.
    """

    simulation: SimPEGGroup


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    # file = r"C:\Users\dominiquef\Desktop\Tests\tile_estimator.ui.json"
    tile_estimator(file)
    sys.stdout.close()
