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

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import copy
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from discretize import TensorMesh, TreeMesh
from geoh5py.objects import Octree
from simpeg import data, data_misfit, maps, meta, objective_function
from simpeg.simulation import BaseSimulation

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.components.factories.simulation_factory import SimulationFactory
from simpeg_drivers.utils.utils import create_nested_mesh


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.components.data import InversionData
    from simpeg_drivers.components.meshes import InversionMesh
    from simpeg_drivers.options import BaseOptions


class MisfitFactory(SimPEGFactory):
    """Build SimPEG global misfit function."""

    def __init__(self, params: BaseParams | BaseOptions, simulation: BaseSimulation):
        """
        :param params: Options object containing SimPEG object parameters.
        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()
        self.factory_type = self.params.inversion_type
        self.simulation = simulation
        self.sorting = None
        self.n_blocks = 3 if self.params.inversion_type == "magnetic vector" else 1

    def concrete_object(self):
        return objective_function.ComboObjectiveFunction

    def build(self, tiles, split_list):  # pylint: disable=arguments-differ
        global_misfit = super().build(
            tiles=tiles,
            split_list=split_list,
        )
        return global_misfit, self.sorting

    def assemble_arguments(  # pylint: disable=arguments-differ
        self,
        tiles,
        split_list,
    ):
        # Base slice over frequencies
        if self.factory_type in ["magnetotellurics", "tipper", "fdem"]:
            channels = self.simulation.survey.frequencies
        else:
            channels = [None]

        futures = []
        tile_count = 0
        data_count = 0
        misfit_count = 0
        # with ProcessPoolExecutor() as executor:
        for local_index in tiles:
            if len(local_index) == 0:
                continue

            n_split = split_list[misfit_count]
            futures.append(
                # executor.submit(
                self.create_nested_misfit(
                    self.simulation,
                    local_index,
                    channels,
                    tile_count,
                    # data_count,
                    n_split,
                    self.params.padding_cells,
                    self.params.inversion_type,
                    self.params.forward_only,
                )
            )
            misfit_count += len(channels)
            data_count += len(local_index)
            tile_count += n_split

        local_misfits = []
        self.sorting = []
        for future in futures:  # as_completed(futures):
            functions, sorting = future  # future.result()
            local_misfits += functions
            self.sorting.append(sorting)

        return [local_misfits]

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""
        return {}

    @classmethod
    def create_nested_misfit(
        cls,
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
        local_sim, _ = create_nested_simulation(
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
            for split_ind in np.array_split(local_index, n_split):
                local_sim, mapping = create_nested_simulation(
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


def create_nested_simulation(
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
    local_survey = create_nested_survey(
        simulation.survey, indices=indices, channel=channel
    )

    if local_mesh is None:
        local_mesh = create_nested_mesh(
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
            simulation.sensitivity_path.parent / f"Tile{tile_id}.zarr"
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


def create_nested_survey(survey, indices, channel=None):
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
            n_verts = locations[0].shape[0]
        else:
            n_verts = locations.shape[0]

        rx_indices = np.arange(n_verts) + location_count

        _, intersect, _ = np.intersect1d(rx_indices, indices, return_indices=True)

        if len(intersect) == 0:
            continue

        location_count += len(intersect)
        receivers = []
        for rx in src.receiver_list:
            # intersect = set(rx.local_index).intersection(indices)
            new_rx = copy(rx)

            if isinstance(rx.locations, tuple | list):  # For MT survey
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

        data_slice = survey.dobs.reshape((n_channels, n_comps, -1), order="F")[
            :, :, indices
        ]
        uncert_slice = survey.std.reshape((n_channels, n_comps, -1), order="F")[
            :, :, indices
        ]

        # For FEM surveys only
        if channel is not None:
            ind = np.where(np.asarray(survey.frequencies) == channel)[0]
            data_slice = data_slice[ind, :, :]
            uncert_slice = uncert_slice[ind, :, :]

        new_survey.dobs = data_slice.flatten(order="F")
        new_survey.std = uncert_slice.flatten(order="F")

    return new_survey


def compute_em_projections(inversion_data, simulation):
    """
    Pre-compute projections for the receivers for efficiency.
    """
    rx_locs = inversion_data.entity.vertices
    projections = {}
    for component in "xyz":
        projections[component] = simulation.mesh.get_interpolation_matrix(
            rx_locs, "faces_" + component[0]
        )

    for source in simulation.survey.source_list:
        for receiver in source.receiver_list:
            projection = 0.0
            for orientation, comp in zip(receiver.orientation, "xyz", strict=True):
                if orientation == 0:
                    continue
                projection += orientation * projections[comp][receiver.local_index, :]
            receiver.spatialP = projection


def compute_dc_projections(inversion_data, simulation, indices):
    """
    Pre-compute projections for the receivers for efficiency.
    """
    rx_locs = inversion_data.entity.vertices
    mn_pairs = inversion_data.entity.cells
    projection = simulation.mesh.get_interpolation_matrix(rx_locs, "nodes")

    for source, ind in zip(simulation.survey.source_list, indices, strict=True):
        proj_mn = projection[mn_pairs[ind, 0], :]

        # Check if dipole receiver
        if not np.all(mn_pairs[ind, 0] == mn_pairs[ind, 1]):
            proj_mn -= projection[mn_pairs[ind, 1], :]

        source.receiver_list[0].spatialP = proj_mn  # pylint: disable=protected-access
