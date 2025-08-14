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

from copy import copy
from pathlib import Path

import numpy as np
from discretize import TreeMesh
from scipy.spatial import cKDTree
from simpeg import data, data_misfit, maps, meta
from simpeg.electromagnetics.frequency_domain.sources import (
    LineCurrent as FEMLineCurrent,
)
from simpeg.electromagnetics.time_domain.sources import LineCurrent as TEMLineCurrent
from simpeg.simulation import BaseSimulation
from simpeg.survey import BaseSurvey

from .surveys import get_intersecting_cells, get_unique_locations


def create_mesh(
    survey: BaseSurvey,
    base_mesh: TreeMesh,
    padding_cells: int = 8,
    minimum_level: int = 4,
    finalize: bool = True,
):
    """
    Create a nested mesh with the same extent as the input global mesh.
    Refinement levels are preserved only around the input locations (local survey).

    Parameters
    ----------

    locations: Array of coordinates for the local survey shape(*, 3).
    base_mesh: Input global TreeMesh object.
    padding_cells: Used for 'method'= 'padding_cells'. Number of cells in each concentric shell.
    minimum_level: Minimum octree level to preserve everywhere outside the local survey area.
    finalize: Return a finalized local treemesh.
    """
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
    local_index,
    channels,
    tile_count,
    # data_count,
    n_split,
    padding_cells,
    inversion_type,
    forward_only,
):
    local_sim, _ = create_simulation(
        simulation,
        None,
        local_index,
        channel=None,
        tile_id=tile_count,
        padding_cells=padding_cells,
    )

    local_mesh = getattr(local_sim, "mesh", None)
    sorting = []
    local_misfits = []
    for count, channel in enumerate(channels):
        for split_ind in np.array_split(local_index, n_split[count]):
            local_sim, mapping = create_simulation(
                simulation,
                local_mesh,
                split_ind,
                channel=channel,
                tile_id=tile_count,
                padding_cells=padding_cells,
            )

            if count == 0:
                sorting.append(split_ind)

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
                if len(channels) > 1:
                    name += f": Channel {channel}"

                lmisfit.name = f"{name}"

            local_misfits.append(lmisfit)

            tile_count += 1

    return local_misfits, sorting


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

    :param inversion_data: InversionData object.
    :param mesh: Octree mesh.
    :param active_cells: Active cell model.
    :param indices: Indices of receivers belonging to the tile.
    :param channel: Channel number for frequency or time channels.
    :param tile_id: Tile id stored on the simulation.
    :param padding_cells: Number of padding cells around the local survey.
    """
    local_survey = create_survey(simulation.survey, indices=indices, channel=channel)

    if local_mesh is None:
        local_mesh = create_mesh(
            local_survey,
            simulation.mesh,
            minimum_level=3,
            padding_cells=padding_cells,
        )

    mapping = maps.TileMap(
        simulation.mesh,
        simulation.active_cells,
        local_mesh,
        enforce_active=True,
        components=3 if getattr(simulation, "model_type", None) == "vector" else 1,
    )

    kwargs = {"survey": local_survey}

    n_actives = int(mapping.local_active.sum())
    if getattr(simulation, "_chiMap", None) is not None:
        if simulation.model_type == "vector":
            kwargs["chiMap"] = maps.IdentityMap(nP=n_actives * 3)
            kwargs["model_type"] = "vector"
        else:
            kwargs["chiMap"] = maps.IdentityMap(nP=n_actives)

        kwargs["active_cells"] = mapping.local_active
        kwargs["sensitivity_path"] = (
            Path(simulation.sensitivity_path).parent / f"Tile{tile_id}.zarr"
        )

    if getattr(simulation, "_rhoMap", None) is not None:
        kwargs["rhoMap"] = maps.IdentityMap(nP=n_actives)
        kwargs["active_cells"] = mapping.local_active
        kwargs["sensitivity_path"] = (
            Path(simulation.sensitivity_path).parent / f"Tile{tile_id}.zarr"
        )

    if getattr(simulation, "_sigmaMap", None) is not None:
        kwargs["sigmaMap"] = maps.ExpMap(local_mesh) * maps.InjectActiveCells(
            local_mesh, mapping.local_active, value_inactive=np.log(1e-8)
        )

    if getattr(simulation, "_etaMap", None) is not None:
        kwargs["etaMap"] = maps.InjectActiveCells(
            local_mesh, mapping.local_active, value_inactive=0
        )
        proj = maps.InjectActiveCells(
            local_mesh,
            mapping.local_active,
            value_inactive=1e-8,
        )
        kwargs["sigma"] = proj * mapping * simulation.sigma

    for key in [
        "max_chunk_sizestore_sensitivities",
        "solver",
        "t0",
        "time_steps",
        "thicknesses",
    ]:
        if hasattr(simulation, key):
            kwargs[key] = getattr(simulation, key)

    local_sim = type(simulation)(local_mesh, **kwargs)

    # TODO bring back
    # inv_type = inversion_data.params.inversion_type
    # if inv_type in ["fdem", "tdem"]:
    #     compute_em_projections(inversion_data, local_sim)
    # elif ("current" in inv_type or "polarization" in inv_type) and (
    #     "2d" not in inv_type or "pseudo" in inv_type
    # ):
    #     compute_dc_projections(inversion_data, local_sim, indices)
    return local_sim, mapping


def create_survey(survey, indices, channel=None):
    """
    Extract source and receivers belonging to the indices.
    """
    sources = []
    location_count = 0
    for src in survey.source_list or [survey.source_field]:
        if channel is not None and getattr(src, "frequency", None) != channel:
            continue

        # Extract the indices of the receivers that belong to this source
        locations = src.receiver_list[0].locations
        if isinstance(locations, tuple | list):  # For MT survey
            n_data = locations[0].shape[0]
        else:
            n_data = locations.shape[0]

        rx_indices = np.arange(n_data) + location_count

        _, intersect, _ = np.intersect1d(rx_indices, indices, return_indices=True)
        location_count += n_data

        if len(intersect) == 0:
            continue

        receivers = []
        for rx in src.receiver_list:
            # intersect = set(rx.local_index).intersection(indices)
            new_rx = copy(rx)

            if isinstance(rx.locations, tuple | list):  # For MT and DC surveys
                new_rx.locations = tuple(loc[intersect] for loc in rx.locations)
            else:
                new_rx.locations = rx.locations[intersect]

            receivers.append(new_rx)

        if any(receivers):
            new_src = copy(src)
            new_src.receiver_list = receivers
            sources.append(new_src)

    if hasattr(survey, "source_field"):
        new_survey = type(survey)(sources[0])
    else:
        new_survey = type(survey)(sources)

    if hasattr(survey, "dobs") and survey.dobs is not None:
        n_channels = len(np.unique(survey.ordering[:, 0]))
        n_comps = len(np.unique(survey.ordering[:, 1]))
        order = "C" if hasattr(survey, "frequencies") else "F"
        data_slice = survey.dobs.reshape((n_channels, n_comps, -1), order=order)[
            :, :, indices
        ]
        uncert_slice = survey.std.reshape((n_channels, n_comps, -1), order=order)[
            :, :, indices
        ]

        # For FEM surveys only
        if channel is not None:
            ind = np.where(np.asarray(survey.frequencies) == channel)[0]
            data_slice = data_slice[ind, :, :]
            uncert_slice = uncert_slice[ind, :, :]

        new_survey.dobs = data_slice.flatten(order=order)
        new_survey.std = uncert_slice.flatten(order=order)

    return new_survey
