# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
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

from __future__ import annotations

import numpy as np
from discretize import TreeMesh
from geoapps_utils.utils.numerical import traveling_salesman
from geoh5py import Workspace
from geoh5py.objects import PotentialElectrode
from scipy.spatial import cKDTree
from simpeg.survey import BaseSurvey


def counter_clockwise_sort(segments: np.ndarray, vertices: np.ndarray) -> np.ndarray:
    """
    Sort segments in counter-clockwise order.

    :param segments: Array of segment indices.
    :param vertices: Array of vertices.

    :return: Sorted segments.
    """
    center = np.mean(vertices, axis=0)
    center_to_vertices = vertices[segments[:, 0], :2] - center[:2]
    deltas = vertices[segments[:, 1], :2] - vertices[segments[:, 0], :2]
    cross = np.cross(center_to_vertices, deltas)

    if np.mean(np.sign(cross[cross != 0])) < 0:
        segments = segments[::-1, ::-1]

    return segments


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

    else:
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
