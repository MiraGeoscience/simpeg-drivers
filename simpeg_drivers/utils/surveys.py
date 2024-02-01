#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved
from __future__ import annotations

from typing import Callable

import numpy as np
from discretize import TensorMesh, TreeMesh
from geoapps_utils.numerical import traveling_salesman
from geoh5py import Workspace
from geoh5py.data import FloatData
from geoh5py.objects import CurrentElectrode, PotentialElectrode
from scipy.spatial import cKDTree
from SimPEG.survey import BaseSurvey


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
    workspace: Workspace,
    survey: PotentialElectrode,
    lines: np.ndarray,
    line_id: int,
    name: str = "Line",
):
    """
    Returns a survey containing data from a single line.

    :param: workspace: geoh5py workspace containing a valid DCIP survey.
    :param: survey: PotentialElectrode object.
    :param: lines: Line indexer for survey.
    :param: line_id: Index of line to extract data from.
    :param: name: Name prefix to assign to the new survey object (to be
        suffixed with the line number).
    """
    current = survey.current_electrodes

    # Extract line locations and store map into full survey
    survey_locs, survey_loc_map = slice_and_map(survey.vertices, lines == line_id)

    # Use line locations to slice cells and store map into full survey
    func = lambda c: (c[0] in survey_loc_map) & (c[1] in survey_loc_map)
    survey_cells, survey_cell_map = slice_and_map(survey.cells, func)
    survey_cells = [[survey_loc_map[i] for i in c] for c in survey_cells]

    # Use line cells to slice ab_cell_ids
    ab_cell_ids = survey.ab_cell_id.values[list(survey_cell_map)]
    ab_cell_ids = np.array(ab_cell_ids, dtype=int) - 1

    # Use line ab_cell_ids to slice current cells
    current_cells, current_cell_map = slice_and_map(
        current.cells, np.unique(ab_cell_ids)
    )

    # Use line current cells to slice current locs
    current_locs, current_loc_map = slice_and_map(
        current.vertices, np.unique(current_cells.ravel())
    )

    # Remap global ids to local counterparts
    ab_cell_ids = np.array([current_cell_map[i] for i in ab_cell_ids])
    current_cells = [[current_loc_map[i] for i in c] for c in current_cells]

    # Save objects
    line_name = f"{name} {line_id}"
    currents = CurrentElectrode.create(
        workspace,
        name=f"{line_name} (currents)",
        vertices=current_locs,
        cells=np.array(current_cells, dtype=np.int32),
        allow_delete=True,
    )
    currents.add_default_ab_cell_id()

    potentials = PotentialElectrode.create(
        workspace,
        name=line_name,
        vertices=survey_locs,
        allow_delete=True,
    )
    potentials.cells = np.array(survey_cells, dtype=np.int32)

    # Add ab_cell_id as referenced data object
    value_map = {k + 1: str(k + 1) for k in ab_cell_ids}
    value_map.update({0: "Unknown"})
    potentials.add_data(
        {
            "A-B Cell ID": {
                "values": np.array(ab_cell_ids + 1, dtype=np.int32),
                "association": "CELL",
                "entity_type": {
                    "primitive_type": "REFERENCED",
                    "value_map": value_map,
                },
            },
            "Global Map": {
                "values": np.array(list(survey_cell_map), dtype=np.int32),
                "association": "CELL",
                "entity_type": {
                    "primitive_type": "REFERENCED",
                    "value_map": {k: str(k) for k in survey_cell_map},
                },
            },
        }
    )

    # Attach current and potential objects and copy data slice into line survey
    potentials.current_electrodes = currents
    for c in survey.children:
        if isinstance(c, FloatData) and "Pseudo" not in c.name:
            potentials.add_data({c.name: {"values": c.values[list(survey_cell_map)]}})

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


def survey_lines(survey, start_loc: list[int | float], save: str | None = None):
    """
    Build an array of line ids for a survey laid out in a line biased grid.

    :param: survey: geoh5py.objects.surveys object with .vertices attribute or xyz array.
    :param: start_loc: Easting and Northing of a survey extremity from which the
        all other survey locations will be traversed and assigned line ids.
    :save: Name assigned to line id (ReferencedData) object if not None.

    """
    # extract xy locations and create linear indexing
    try:
        locs = survey.vertices[:, :2]
    except AttributeError:
        locs = survey[:, :2]

    nodes = np.arange(len(locs)).tolist()

    # find the id of the closest point to the starting location
    start_id = np.argmin(np.linalg.norm(locs - start_loc, axis=1))

    # pop the starting location and index out of their respective lists
    locs = locs.tolist()
    loc = locs[start_id]
    inds = []
    n = nodes.pop(start_id)
    inds.append(n)

    # compute the tree of the remaining points and begin to traverse the tree
    # in the direction of closest neighbors.  Label points with same line id
    # until an outlier is detected in the distance to the next closest point,
    # then increase the line id.
    tree = cKDTree(locs)
    line_id = 1  # zero is reserved
    lines = []
    distances = []
    while nodes:
        lines.append(line_id)
        dist, next_id = next_neighbor(tree, loc, nodes)

        outlier = False
        if len(distances) > 1:
            if np.allclose(dist, distances, atol=1e-6):
                outlier = False
            else:
                outlier = is_outlier(distances, dist)

        if outlier:
            line_id += 1
            distances = []
        else:
            distances.append(dist)

        n = nodes.pop(nodes.index(next_id))
        inds.append(n)
        loc = locs[next_id]

    lines += [line_id]  # nodes run out before last id assigned

    inds = np.argsort(inds)
    if save is not None:
        survey.add_data(
            {
                save: {
                    "values": np.array(lines)[inds],
                    "association": "VERTEX",
                    "entity_type": {
                        "primitive_type": "REFERENCED",
                        "value_map": {k: str(k) for k in lines},
                    },
                }
            }
        )

    return np.array(lines)[inds]
