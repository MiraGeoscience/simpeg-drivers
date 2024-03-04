#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved
from __future__ import annotations

import warnings
from typing import Callable

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    from sklearn.cluster import KMeans  # pylint: disable=import-error

import numpy as np
from discretize import TreeMesh
from geoapps_utils.numerical import running_mean, traveling_salesman
from geoh5py import Workspace
from geoh5py.objects import PotentialElectrode
from scipy.interpolate import interp1d
from scipy.spatial import cKDTree
from SimPEG.survey import BaseSurvey


class DistanceMapper:
    """
    Class to map distances to locations.
    """

    def __init__(self, locations: np.ndarray, smoothing: int = 0):
        if not isinstance(locations, np.ndarray) or locations.ndim != 2:
            raise ValueError("Locations must be a 2D array.")

        order = traveling_salesman(locations)
        self.locations = locations[order, :]
        self._profile: np.ndarray | None = None
        self._smooth_locations: np.ndarray | None = None
        self.smoothing = smoothing

    @property
    def smoothing(self) -> int:
        """
        Smoothing factor.
        """
        return self._smoothing

    @smoothing.setter
    def smoothing(self, value: int):
        """
        Smoothing factor.
        """
        if not isinstance(value, int):
            raise ValueError("Smoothing must be an integer.")

        self._smoothing: int = value
        self._smooth_locations = None
        self._profile = None

    @property
    def smooth_locations(self) -> np.ndarray:
        """
        Smoothed 3D coordinate locations.
        """
        if self._smooth_locations is None:
            smooth_locations = np.c_[
                [running_mean(locs, self.smoothing) for locs in self.locations.T]
            ].T
            smooth_locations[0, :] = self.locations[0, :]
            smooth_locations[-1, :] = self.locations[-1, :]
            self._smooth_locations = smooth_locations
        return self._smooth_locations

    @property
    def profile(self) -> np.ndarray:
        """
        Along line profile of distance and elevation.
        """
        if self._profile is None:
            self._profile = compute_alongline_distance(self.smooth_locations)
        return self._profile

    @property
    def distances(self) -> np.ndarray:
        """
        Along line distances.
        """
        return self.profile[:, 0]

    def map_locations(self, distance: np.ndarray | None = None) -> np.ndarray:
        """
        Interpolate 3D coordinates from distance along profile.
        """
        if distance is None:
            return self.smooth_locations

        return np.c_[
            [
                interp1d(self.distances, locs, fill_value="extrapolate")(distance)
                for locs in self.smooth_locations.T
            ]
        ].T


def compute_alongline_distance(points: np.ndarray, ordered: bool = True):
    """
    Convert from cartesian (x, y, values) points to (distance, values) locations.

    :param: points: Cartesian coordinates of points lying either roughly within a
        plane or a line.
    """
    if not ordered:
        order = traveling_salesman(points)
        points = points[order, :]

    distances = np.cumsum(
        np.r_[0, np.linalg.norm(np.diff(points[:, :2], axis=0), axis=1)]
    )
    if points.shape[1] == 3:
        distances = np.c_[distances, points[:, 2:]]

    return distances


def extract_dcip_survey(
    workspace: Workspace, survey: PotentialElectrode, cell_mask: np.ndarray
):
    """
    Returns a survey containing data from a single line.

    :param workspace: geoh5py workspace containing a valid DCIP survey.
    :param survey: PotentialElectrode object.
    :param cell_mask: Boolean array of M-N pairs to include in the new survey.
    """

    if not np.any(cell_mask):
        raise ValueError("No cells found in the mask.")

    active_poles = np.zeros(survey.n_vertices, dtype=bool)

    if survey.cells is not None:
        active_poles[survey.cells[cell_mask, :].ravel()] = True

    potentials = survey.copy(parent=workspace, mask=active_poles, cell_mask=cell_mask)

    return potentials


def get_intersecting_cells(locations: np.ndarray, mesh: TreeMesh) -> np.ndarray:
    """
    Find cells that intersect with a set of segments.

    :param: locations: Locations making a line path.
    :param: mesh: TreeMesh object.

    :return: Array of unique cell indices.
    """
    cell_index = []
    for ind in range(locations.shape[0] - 1):
        cell_index.append(mesh.get_cells_along_line(locations[ind], locations[ind + 1]))

    return np.unique(np.hstack(cell_index))


def get_unique_locations(survey: BaseSurvey) -> np.ndarray:
    """
    Get unique locations from a survey including sources and receivers when
    applicable.

    :param: survey: SimPEG survey object.

    :return: Array of unique locations.
    """
    if survey.source_list:
        locations = []
        for source in survey.source_list:
            source_location = source.location
            if source_location is not None:
                if not isinstance(source_location, list):
                    locations += [[source_location]]
                else:
                    locations += [source_location]
            locations += [receiver.locations for receiver in source.receiver_list]
        locations = np.vstack([np.vstack(np.atleast_2d(*locs)) for locs in locations])
    else:
        locations = survey.receiver_locations

    return np.unique(locations, axis=0)


def is_outlier(population: list[float | int], value: float, n_std: int | float = 3):
    """
    use a standard deviation threshold to determine if value is an outlier for the population.

    :param population: list of values.
    :param value: single value to detect outlier status
    :param n_std (optional):

    :return True if the deviation of value from the mean exceeds the standard deviation threshold.
    """
    mean = np.mean(population)
    std = np.std(population)
    deviation = np.abs(mean - value)
    return deviation > n_std * std


def next_neighbor(tree: cKDTree, point: list[float], nodes: list[int], n: int = 3):
    """
    Returns smallest distance neighbor that has not yet been traversed.

    :param: tree: kd-tree computed for the point cloud of possible neighbors.
    :param: point: Current point being traversed.
    :param: nodes: Traversed point ids.
    """
    distances, neighbors = tree.query(point, n)
    new_ids = new_neighbors(distances, neighbors, nodes)
    if any(new_ids):
        distances = distances[new_ids]
        neighbors = neighbors[new_ids]
        next_id = np.argmin(distances)
        return distances[next_id], neighbors[next_id]

    return next_neighbor(tree, point, nodes, n + 3)


def new_neighbors(distances: np.ndarray, neighbors: np.ndarray, nodes: list[int]):
    """
    Index into neighbor arrays excluding zero distance and past neighbors.

    :param: distances: previously computed distances
    :param: neighbors: Possible neighbors
    :param: nodes: Traversed point ids.
    """
    ind = [
        i in nodes if distances[neighbors.tolist().index(i)] != 0 else False
        for i in neighbors
    ]
    return np.where(ind)[0].tolist()


def slice_and_map(obj: np.ndarray, slicer: np.ndarray | Callable):
    """
    Slice an array and return both sliced array and global to local map.

    :param object: Array to be sliced.
    :param slicer: Boolean index array, Integer index array,  or callable
        that provides a condition to keep or remove each row of object.
    :return: Sliced array.
    :return: Dictionary map from global to local indices.
    """

    if isinstance(slicer, np.ndarray):
        if slicer.dtype == bool:
            sliced_object = obj[slicer]
            g2l = dict(zip(np.where(slicer)[0], np.arange(len(obj))))
        else:
            sliced_object = obj[slicer]
            g2l = dict(zip(slicer, np.arange(len(slicer))))

    elif callable(slicer):
        slicer = np.array([slicer(k) for k in obj])
        sliced_object = obj[slicer]
        g2l = dict(zip(np.where(slicer)[0], np.arange(len(obj))))

    return sliced_object, g2l


def tile_locations(
    locations,
    n_tiles,
):
    """
    Function to tile a survey points into smaller square subsets of points

    :param numpy.ndarray locations: n x 2 array of locations [x,y]
    :param integer n_tiles: number of tiles (for 'cluster'), or number of
        refinement steps ('other')
    :param bounding_box: bool [False]
        Return the SW and NE corners of each tile.
    :param count: bool [False]
        Return the number of locations in each tile.
    :param unique_id: bool [False]
        Return the unique identifiers of all tiles.

    :returns tiles: list of numpy.ndarray
        List of arrays containing the indices of the points in each tile.
    """
    np.random.seed(0)
    # Cluster
    # TODO turn off filter once sklearn has dealt with the issue causing the warning
    cluster = KMeans(n_clusters=n_tiles, n_init="auto")
    cluster.fit_predict(locations[:, :2])

    labels = cluster.labels_
    # Get the tile numbers that exist, for compatibility with the next method
    tile_id = np.unique(cluster.labels_)
    tiles = [np.where(labels == tid)[0] for tid in tile_id]

    return tiles
