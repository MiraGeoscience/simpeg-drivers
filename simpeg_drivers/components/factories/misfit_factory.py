# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part simpeg-drivers package.                                        '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.components.data import InversionData

import numpy as np
from geoh5py.objects import Octree
from simpeg import data, data_misfit, maps, objective_function

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


class MisfitFactory(SimPEGFactory):
    """Build SimPEG global misfit function."""

    def __init__(self, params: BaseParams, models=None):
        """
        :param params: Params object containing SimPEG object parameters.
        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()
        self.factory_type = self.params.inversion_type
        self.models = models
        self.sorting = None
        self.ordering = None

    def concrete_object(self):
        return objective_function.ComboObjectiveFunction

    def build(self, tiles, inversion_data, mesh, active_cells):  # pylint: disable=arguments-differ
        global_misfit = super().build(
            tiles=tiles,
            inversion_data=inversion_data,
            mesh=mesh,
            active_cells=active_cells,
        )
        return global_misfit, self.sorting, self.ordering

    def assemble_arguments(  # pylint: disable=arguments-differ
        self,
        tiles,
        inversion_data,
        mesh,
        active_cells,
    ):
        # Base slice over frequencies
        if self.factory_type in ["magnetotellurics", "tipper", "fem"]:
            channels = np.unique([list(v) for v in inversion_data.observed.values()])
        else:
            channels = [None]

        local_misfits = []
        self.sorting = []
        self.ordering = []
        tile_num = 0
        data_count = 0
        for tile_count, local_index in enumerate(tiles):
            if len(local_index) == 0:
                continue

            for count, channel in enumerate(channels):
                local_sim, local_index, ordering, mapping = (
                    self.create_nested_simulation(
                        inversion_data,
                        mesh,
                        active_cells,
                        local_index,
                        channel=channel,
                        tile_id=tile_num,
                        padding_cells=self.params.padding_cells,
                    )
                )

                if count == 0:
                    if self.factory_type in [
                        "fem",
                        "tdem",
                        "magnetotellurics",
                        "tipper",
                    ]:
                        self.sorting.append(
                            np.arange(
                                data_count,
                                data_count + len(local_index),
                                dtype=int,
                            )
                        )
                        data_count += len(local_index)
                    else:
                        self.sorting.append(local_index)

                if "induced polarization" in self.params.inversion_type:
                    if "2d" in self.params.inversion_type:
                        proj = maps.InjectActiveCells(
                            mesh, active_cells, valInactive=1e-8
                        )
                    else:
                        proj = maps.InjectActiveCells(
                            mapping.local_mesh,
                            mapping.local_active,
                            valInactive=1e-8,
                        )

                    # TODO this should be done in the simulation factory
                    local_sim.sigma = proj * mapping * self.models.conductivity

                # TODO add option to export tile meshes
                # from octree_creation_app.utils import treemesh_2_octree
                # from geoh5py.shared.utils import fetch_active_workspace
                #
                # with fetch_active_workspace(self.params.geoh5) as ws:
                #     treemesh_2_octree(ws, local_sim.mesh)

                # TODO Parse workers to simulations
                local_sim.workers = self.params.distributed_workers
                local_data = data.Data(local_sim.survey)

                if self.params.forward_only:
                    lmisfit = data_misfit.L2DataMisfit(
                        local_data, local_sim, model_map=mapping
                    )

                else:
                    local_data.dobs = local_sim.survey.dobs
                    local_data.standard_deviation = local_sim.survey.std
                    lmisfit = data_misfit.L2DataMisfit(
                        data=local_data,
                        simulation=local_sim,
                        model_map=mapping,
                    )
                    lmisfit.W = 1 / local_sim.survey.std
                    name = self.params.inversion_type

                    if len(tiles) > 1:
                        name += f": Tile {tile_count + 1}"
                    if len(channels) > 1:
                        name += f": Channel {channel}"

                    lmisfit.name = f"{name}"
                local_misfits.append(lmisfit)
                self.ordering.append(ordering)
                tile_num += 1

        return [local_misfits]

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""
        return {}

    @staticmethod
    def create_nested_simulation(
        inversion_data: InversionData,
        mesh: Octree,
        active_cells: np.ndarray,
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
        survey, indices, ordering = inversion_data.create_survey(
            mesh=mesh, local_index=indices, channel=channel
        )
        local_sim, mapping = inversion_data.simulation(
            mesh,
            active_cells,
            survey,
            tile_id=tile_id,
            padding_cells=padding_cells,
        )

        return local_sim, indices, ordering, mapping
