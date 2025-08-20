# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
from __future__ import annotations

import warnings
from copy import copy
from pathlib import Path

import numpy as np
from discretize import TensorMesh, TreeMesh
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from simpeg import data, data_misfit, maps, meta
from simpeg.electromagnetics.base_1d import BaseEM1DSimulation
from simpeg.electromagnetics.frequency_domain.simulation import BaseFDEMSimulation
from simpeg.electromagnetics.frequency_domain.sources import (
    LineCurrent as FEMLineCurrent,
)
from simpeg.electromagnetics.natural_source import Simulation3DPrimarySecondary
from simpeg.electromagnetics.static.induced_polarization.simulation import (
    Simulation3DNodal as Simulation3DIP,
)
from simpeg.electromagnetics.static.resistivity.simulation import (
    Simulation3DNodal as Simulation3DRes,
)
from simpeg.electromagnetics.time_domain.simulation import BaseTDEMSimulation
from simpeg.electromagnetics.time_domain.sources import LineCurrent as TEMLineCurrent
from simpeg.simulation import BaseSimulation
from simpeg.survey import BaseSurvey

from simpeg_drivers.utils.surveys import (
    compute_dc_projections,
    compute_em_projections,
    get_intersecting_cells,
    get_unique_locations,
)


def create_mesh(
    survey: BaseSurvey,
    base_mesh: TreeMesh | TensorMesh,
    padding_cells: int = 8,
    minimum_level: int = 4,
    finalize: bool = True,
) -> TreeMesh | TensorMesh:
    """
    Create a nested mesh with the same extent as the input global mesh.
    Refinement levels are preserved only around the input locations (local survey).


    :param survey: SimPEG survey object.
    :param base_mesh: Input global TreeMesh object.
    :param padding_cells: Used for 'method'= 'padding_cells'. Number of cells in each concentric shell.
    :param minimum_level: Minimum octree level to preserve everywhere outside the local survey area.
    :param finalize: Return a finalized local treemesh.

    :return: A TreeMesh object with the same extent as the input global mesh.
    """
    if not isinstance(base_mesh, TreeMesh):
        return base_mesh

    locations = get_unique_locations(survey)
    nested_mesh = TreeMesh(
        [base_mesh.h[0], base_mesh.h[1], base_mesh.h[2]],
        x0=base_mesh.x0,
        diagonal_balance=False,
    )
    base_level = base_mesh.max_level - minimum_level
    base_refinement = base_mesh.cell_levels_by_index(np.arange(base_mesh.nC))
    base_refinement[base_refinement > base_level] = base_level
    nested_mesh.insert_cells(
        base_mesh.gridCC,
        base_refinement,
        finalize=False,
    )
    base_cell = np.min([base_mesh.h[0][0], base_mesh.h[1][0]])
    tx_loops = []
    for source in survey.source_list:
        if isinstance(source, TEMLineCurrent | FEMLineCurrent):
            mesh_indices = get_intersecting_cells(source.location, base_mesh)
            tx_loops.append(base_mesh.cell_centers[mesh_indices, :])

    if tx_loops:
        locations = np.vstack([locations, *tx_loops])

    tree = cKDTree(locations[:, :2])
    rad, _ = tree.query(base_mesh.gridCC[:, :2])
    pad_distance = 0.0
    for ii in range(minimum_level):
        pad_distance += base_cell * 2**ii * padding_cells
        indices = np.where(rad < pad_distance)[0]
        levels = base_mesh.cell_levels_by_index(indices)
        levels[levels > (base_mesh.max_level - ii)] = base_mesh.max_level - ii
        nested_mesh.insert_cells(
            base_mesh.gridCC[indices, :],
            levels,
            finalize=False,
        )

    if finalize:
        nested_mesh.finalize()

    return nested_mesh


def create_misfit(
    simulation,
    local_indices,
    channel,
    tile_count,
    n_split,
    padding_cells,
    inversion_type,
    forward_only,
):
    """
    Create a list of local misfits based on the local indices.

    The local indices are further split into smaller chunks if requested, sharing
    the same mesh.

    :param simulation: SimPEG simulation object.
    :param local_indices: Indices of the receiver locations belonging to the tile.
    :param channel: Channel of the simulationm, for frequency systems only.
    :param tile_count: Current tile ID, used to name the file on disk and for sampling
      of topography for 1D simulations.
    :param n_split: Number of splits to create for the local indices.
    :param padding_cells: Number of padding cells around the local survey.
    :param inversion_type: Type of inversion, used to name the misfit (joint inversion).
    :param forward_only: If False, data is transferred to the local simulation.

    :return: List of local misfits and data slices.
    """
    local_sim, _, _ = create_simulation(
        simulation,
        None,
        local_indices,
        channel=channel,
        tile_id=tile_count,
        padding_cells=padding_cells,
    )

    local_mesh = getattr(local_sim, "mesh", None)
    local_misfits = []
    data_slices = []
    for split_ind in np.array_split(local_indices, n_split):
        local_sim, mapping, data_slice = create_simulation(
            simulation,
            local_mesh,
            split_ind,
            channel=channel,
            tile_id=tile_count,
            padding_cells=padding_cells,
        )
        meta_simulation = meta.MetaSimulation(
            simulations=[local_sim], mappings=[mapping]
        )

        local_data = data.Data(local_sim.survey)
        lmisfit = data_misfit.L2DataMisfit(local_data, meta_simulation)
        if not forward_only:
            local_data.dobs = local_sim.survey.dobs
            local_data.standard_deviation = local_sim.survey.std
            name = inversion_type
            name += f": Tile {tile_count + 1}"
            if channel is not None:
                name += f": Channel {channel}"

            lmisfit.name = f"{name}"

        local_misfits.append(lmisfit)
        data_slices.append(data_slice)

        tile_count += 1

    return local_misfits, data_slices


def create_simulation(
    simulation: BaseSimulation,
    local_mesh: TreeMesh | None,
    indices: np.ndarray,
    *,
    channel: int | None = None,
    tile_id: int | None = None,
    padding_cells=100,
):
    """
    Generate a survey, mesh and simulation based on indices.

    :param simulation: SimPEG.simulation object.
    :param local_mesh: Local mesh for the simulation, else created.
    :param indices: Indices of receivers belonging to the tile.
    :param channel: Channel of the simulation, for frequency simulations only.
    :param tile_id: Tile id stored on the simulation.
    :param padding_cells: Number of padding cells around the local survey.

    :return: Local simulation, mapping and local ordering.
    """
    local_survey, local_ordering = create_survey(
        simulation.survey, indices=indices, channel=channel
    )
    kwargs = {"survey": local_survey}

    if local_mesh is None:
        local_mesh = create_mesh(
            local_survey,
            simulation.mesh,
            minimum_level=3,
            padding_cells=padding_cells,
        )

    args = (local_mesh,)
    if isinstance(simulation, BaseEM1DSimulation):
        local_mesh = simulation.layers_mesh
        actives = np.ones(simulation.layers_mesh.n_cells, dtype=bool)
        model_slice = np.arange(
            tile_id, simulation.mesh.n_cells, simulation.mesh.shape_cells[0]
        )[::-1]
        mapping = maps.Projection(simulation.mesh.n_cells, model_slice)
        kwargs["topo"] = simulation.active_cells[tile_id]
        args = ()

    elif isinstance(local_mesh, TreeMesh):
        mapping = maps.TileMap(
            simulation.mesh,
            simulation.active_cells,
            local_mesh,
            enforce_active=True,
            components=3 if getattr(simulation, "model_type", None) == "vector" else 1,
        )
        actives = mapping.local_active
    # For DCIP-2D
    else:
        actives = simulation.active_cells
        mapping = maps.IdentityMap(nP=int(actives.sum()))

    n_actives = int(actives.sum())
    if getattr(simulation, "_chiMap", None) is not None:
        if simulation.model_type == "vector":
            kwargs["chiMap"] = maps.IdentityMap(nP=n_actives * 3)
            kwargs["model_type"] = "vector"
        else:
            kwargs["chiMap"] = maps.IdentityMap(nP=n_actives)

        kwargs["active_cells"] = actives
        kwargs["sensitivity_path"] = (
            Path(simulation.sensitivity_path).parent / f"Tile{tile_id}.zarr"
        )

    if getattr(simulation, "_rhoMap", None) is not None:
        kwargs["rhoMap"] = maps.IdentityMap(nP=n_actives)
        kwargs["active_cells"] = actives
        kwargs["sensitivity_path"] = (
            Path(simulation.sensitivity_path).parent / f"Tile{tile_id}.zarr"
        )

    if getattr(simulation, "_sigmaMap", None) is not None:
        kwargs["sigmaMap"] = maps.ExpMap(local_mesh) * maps.InjectActiveCells(
            local_mesh, actives, value_inactive=np.log(1e-8)
        )

    if getattr(simulation, "_etaMap", None) is not None:
        kwargs["etaMap"] = maps.InjectActiveCells(local_mesh, actives, value_inactive=0)
        proj = maps.InjectActiveCells(
            local_mesh,
            actives,
            value_inactive=1e-8,
        )
        kwargs["sigma"] = proj * mapping * simulation.sigma[simulation.active_cells]

    for key in [
        "max_chunk_sizestore_sensitivities",
        "solver",
        "t0",
        "time_steps",
        "thicknesses",
    ]:
        if hasattr(simulation, key):
            kwargs[key] = getattr(simulation, key)

    local_sim = type(simulation)(*args, **kwargs)

    if isinstance(
        simulation, BaseFDEMSimulation | BaseTDEMSimulation
    ) and not isinstance(simulation, Simulation3DPrimarySecondary):
        compute_em_projections(simulation.survey.locations, local_sim)
    elif isinstance(simulation, Simulation3DRes | Simulation3DIP):
        compute_dc_projections(
            simulation.survey.locations, simulation.survey.cells, local_sim
        )
    return local_sim, mapping, local_ordering


def create_survey(survey, indices, channel=None):
    """
    Extract source and receivers belonging to the indices.

    :param survey: SimPEG survey object.
    :param indices: Indices of the receivers belonging to the tile.
    :param channel: Channel of the survey, for frequency systems only.
    """
    sources = []

    # Return the subset of data that belongs to the tile
    slice_inds = np.isin(survey.ordering[:, 2], indices)
    if channel is not None:
        ind = np.where(np.asarray(survey.frequencies) == channel)[0]
        slice_inds *= np.isin(survey.ordering[:, 0], ind)

    for src in survey.source_list or [survey.source_field]:
        if channel is not None and getattr(src, "frequency", None) != channel:
            continue

        # Extract the indices of the receivers that belong to this source
        _, intersect, _ = np.intersect1d(src.rx_ids, indices, return_indices=True)

        if len(intersect) == 0:
            continue

        receivers = []
        for rx in src.receiver_list:
            new_rx = copy(rx)

            # For MT and DC surveys with multiple locations per receiver
            if isinstance(rx.locations, tuple | list):
                new_rx.locations = tuple(loc[intersect] for loc in rx.locations)
            else:
                new_rx.locations = rx.locations[intersect]

            receivers.append(new_rx)

        if any(receivers):
            new_src = copy(src)
            new_src.rx_ids = src.rx_ids[intersect]
            new_src.receiver_list = receivers
            sources.append(new_src)

    if hasattr(survey, "source_field"):
        new_survey = type(survey)(sources[0])
    else:
        new_survey = type(survey)(sources)

    if hasattr(survey, "dobs") and survey.dobs is not None:
        # For FEM surveys only
        new_survey.dobs = survey.dobs[
            survey.ordering[slice_inds, 0],
            survey.ordering[slice_inds, 1],
            survey.ordering[slice_inds, 2],
        ]
        new_survey.std = survey.std[
            survey.ordering[slice_inds, 0],
            survey.ordering[slice_inds, 1],
            survey.ordering[slice_inds, 2],
        ]

    return new_survey, survey.ordering[slice_inds, :]


def tile_locations(
    locations: np.ndarray,
    n_tiles: int,
    labels: np.ndarray | None = None,
    sorting: np.ndarray | None = None,
) -> list[np.ndarray]:
    """
    Function to tile a survey points into smaller square subsets of points using
    a k-means clustering approach.

    If labels are provided and the number of unique labels is less than or equal to
    the number of tiles, the function will return an even split of the unique labels.

    :param locations: Array of locations.
    :param n_tiles: Number of tiles (for 'cluster')
    :param labels: Array of values to append to the locations
    :param sorting: Array of indices to sort the locations before clustering.

    :return: List of arrays containing the indices of the points in each tile.
    """
    grid_locs = locations[:, :2].copy()

    if labels is not None:
        if len(labels) != grid_locs.shape[0]:
            raise ValueError(
                "Labels array must have the same length as the locations array."
            )

        if len(np.unique(labels)) >= n_tiles:
            label_groups = np.array_split(np.unique(labels), n_tiles)
            return [np.where(np.isin(labels, group))[0] for group in label_groups]

        # Normalize location coordinates to [0, 1] range
        grid_locs -= grid_locs.min(axis=0)
        max_val = grid_locs.max(axis=0)
        grid_locs[:, max_val > 0] /= max_val[max_val > 0]
        grid_locs = np.c_[grid_locs, labels]

    if sorting is not None:
        grid_locs = grid_locs[sorting, :]

    # Cluster
    # TODO turn off filter once sklearn has dealt with the issue causing the warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        from sklearn.cluster import KMeans

        kmeans = KMeans(n_clusters=n_tiles, random_state=0, n_init="auto")
        cluster_size = int(np.ceil(grid_locs.shape[0] / n_tiles))
        kmeans.fit(grid_locs)

    if labels is not None:
        cluster_id = kmeans.labels_
    else:
        # Redistribute cluster centers to even out the number of points
        centers = kmeans.cluster_centers_
        centers = (
            centers.reshape(-1, 1, grid_locs.shape[1])
            .repeat(cluster_size, 1)
            .reshape(-1, grid_locs.shape[1])
        )
        distance_matrix = cdist(grid_locs, centers)
        cluster_id = linear_sum_assignment(distance_matrix)[1] // cluster_size

    tiles = []
    for tid in set(cluster_id):
        tiles += [np.where(cluster_id == tid)[0]]

    return tiles
