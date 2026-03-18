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

import numpy as np
from discretize import TreeMesh
from geoh5py import Workspace
from geoh5py.data import IntegerData
from geoh5py.objects import DrapeModel, PotentialElectrode
from geoh5py.shared.merging.drape_model import DrapeModelMerger
from scipy.sparse import csgraph, csr_matrix
from scipy.spatial import cKDTree
from simpeg.survey import BaseSurvey

from simpeg_drivers.options import (
    DrapeModelOptions,
)
from simpeg_drivers.utils.utils import get_drape_model


def station_spacing(
    locations: np.ndarray,
    statistic: str = "median",
) -> float:
    """
    Compute smallest station spacings and return statistic on the collection.

    :param locations: Array of locations representing a geophysical survey.
    :param statistic: Name of numpy statistic to compute on the collection.
    """

    tree = cKDTree(locations)
    distances, _ = tree.query(locations, k=2)

    if statistic not in ["median", "mean", "min", "max"]:
        raise ValueError(
            "Invalid statistic.  Options include 'median', 'mean', 'min', 'max'."
        )

    return getattr(np, statistic)(distances[:, 1])


def counter_clockwise_sort(segments: np.ndarray, vertices: np.ndarray) -> np.ndarray:
    """
    Sort segments in counter-clockwise order.

    :param segments: Array of segment indices.
    :param vertices: Array of vertices.

    :return: Sorted segments.
    """
    center = np.mean(vertices[segments[:, 0], :2], axis=0)
    center_to_vertices = vertices[segments[:, 0], :2] - center[:2]
    deltas = vertices[segments[:, 1], :2] - vertices[segments[:, 0], :2]
    cross = np.cross(center_to_vertices, deltas)

    if np.mean(np.sign(cross[cross != 0])) < 0:
        segments = segments[::-1, ::-1]

    return segments


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


def get_parts_from_electrodes(survey: PotentialElectrode) -> np.ndarray:
    """
    Get part numbers from a survey containing PotentialElectrode objects.

    :param survey: PotentialElectrode survey object.

    :return: Array of part numbers corresponding to each cell in the survey.
    """
    edge_array = csr_matrix(
        (
            np.ones(survey.n_cells * 2),
            (
                np.kron(survey.cells[:, 0], [1, 1]),
                survey.cells.flatten(),
            ),
        ),
        shape=(survey.n_vertices, survey.n_vertices),
    )

    connections = csgraph.connected_components(edge_array)[1]
    parts = connections[survey.cells[:, 0]]
    _, u_part = np.unique(parts, return_inverse=True)
    return u_part


def compute_em_projections(locations, simulation):
    """
    Pre-compute projections for the receivers for efficiency.
    """
    projections = {}
    for component in "xyz":
        projections[component] = simulation.mesh.get_interpolation_matrix(
            locations, "faces_" + component[0]
        )

    for source in simulation.survey.source_list:
        indices = source.rx_ids
        for receiver in source.receiver_list:
            projection = 0.0
            for orientation, comp in zip(receiver.orientation, "xyz", strict=True):
                if orientation == 0:
                    continue
                projection += orientation * projections[comp][indices, :]
            receiver.spatialP = projection


def compute_dc_projections(locations, cells, simulation):
    """
    Pre-compute projections for the receivers for efficiency.
    """
    projection = simulation.mesh.get_interpolation_matrix(locations, "nodes")

    for source in simulation.survey.source_list:
        indices = source.rx_ids
        for receiver in source.receiver_list:
            proj_mn = projection[cells[indices, 0], :]

            # Check if dipole receiver
            if not np.all(cells[indices, 0] == cells[indices, 1]):
                proj_mn -= projection[cells[indices, 1], :]

            receiver.spatialP = proj_mn  # pylint: disable=protected-access


def create_mesh_by_line_id(
    workspace: Workspace,
    survey: PotentialElectrode,
    line_ids: np.ndarray,
    drape_options: DrapeModelOptions,
    **object_kwargs,
) -> DrapeModel:
    """
    Create a drape mesh for the dc resistivity survey lines.

    :param workspace: Workspace to create the drape mesh in.
    :param survey: PotentialElectrode survey object.
    :param line_ids: Array containing the line IDs for each vertex.
    :param drape_options: DrapeModelOptions containing the parameters for the drape mesh
    :param object_kwargs: Additional keyword arguments to pass to the DrapeModelMerger.create_object method.

    :return: A DrapeModel object containing the merged drape mesh for all survey lines.
    """
    drape_models = []
    temp_work = Workspace()

    relief = get_max_line_relief(survey, line_ids, drape_options.v_cell_size)

    for line_id in np.unique(line_ids):
        poles = get_poles_by_line_id(survey, line_ids, line_id)
        poles = np.unique(poles, axis=0)
        poles = normalize_vertically(poles, relief)

        drape_model = get_drape_model(
            temp_work,
            poles,
            [
                drape_options.u_cell_size,
                drape_options.v_cell_size,
            ],
            drape_options.depth_core,
            [drape_options.horizontal_padding] * 2
            + [drape_options.vertical_padding, 1],
            drape_options.expansion_factor,
        )
        drape_models.append(drape_model)

    entity = DrapeModelMerger.create_object(workspace, drape_models, **object_kwargs)

    return entity


def get_max_line_relief(
    survey: PotentialElectrode, line_ids: np.ndarray, z_cell_size: float
) -> float:
    """
    Get the maximum relief across all survey lines, rounded to the nearest cell thickness.

    :param survey: PotentialElectrode survey object.
    :param line_ids: Array containing the line IDs for each vertex.
    :param z_cell_size: Cell size in the vertical direction for the drape mesh.
    """
    max_relief = 0
    for line_id in np.unique(line_ids):
        poles = get_poles_by_line_id(survey, line_ids, line_id)
        max_relief = np.maximum(poles[:, 2].max() - poles[:, 2].min(), max_relief)

    return (max_relief // z_cell_size + 2) * z_cell_size


def get_poles_by_line_id(
    survey: PotentialElectrode, line_ids: np.ndarray, uid: int
) -> np.ndarray:
    """
    Get the vertices associated with a given line ID.

    :param survey: PotentialElectrode survey object.
    :param line_ids: Array containing the line IDs for each vertex.
    :param uid: Unique ID for the survey line.

    :return: Array containing the receiver and transmitter pole locations associated with a given line ID.
    """
    mn_mask = line_ids == uid

    unique_tx = np.unique(survey.ab_cell_id.values[mn_mask])

    ab_mask = np.isin(survey.complement.ab_cell_id.values, unique_tx)

    return np.vstack(
        [
            survey.vertices[survey.cells[mn_mask].flatten()],
            survey.current_electrodes.vertices[
                survey.current_electrodes.cells[ab_mask].flatten()
            ],
        ]
    )


def normalize_vertically(poles: np.ndarray, relief: float) -> np.ndarray:
    """
    Given a set of pole locations, normalize the vertical component to the maximum relief across all lines.

    This ensures that the drape mesh has uniform vertical discretization across all survey lines.

    :param poles: Array of pole locations to normalize.
    :param relief: Maximum relief across all survey lines, rounded to the nearest cell thickness.

    :return: Array of pole locations with normalized vertical component.
    """
    min_poles_z = poles[:, 2].min()
    poles[:, 2] -= min_poles_z
    poles[:, 2] *= relief / np.maximum(poles[:, 2].max(), 1e-3)

    # Shift back vertically
    poles[:, 2] += min_poles_z

    return poles
