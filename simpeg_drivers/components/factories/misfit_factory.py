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

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

import numpy as np
from simpeg import data, data_misfit, objective_function

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
        padding_cells = 4 if self.factory_type in ["fem", "tdem"] else 6

        # Keep whole mesh for 1 tile
        if len(tiles) == 1:
            padding_cells = 100

        tile_num = 0
        data_count = 0
        for tile_count, local_index in enumerate(tiles):
            if len(local_index) == 0:
                continue

            for count, channel in enumerate(channels):
                survey, local_index, ordering = inversion_data.create_survey(
                    mesh=mesh, local_index=local_index, channel=channel
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

                local_sim, local_map = inversion_data.simulation(
                    mesh,
                    active_cells,
                    survey,
                    self.models,
                    tile_id=tile_num,
                    padding_cells=padding_cells,
                )

                # TODO add option to export tile meshes
                # from octree_creation_app.utils import treemesh_2_octree
                # from geoh5py.shared.utils import fetch_active_workspace
                #
                # with fetch_active_workspace(self.params.geoh5) as ws:
                #     treemesh_2_octree(ws, local_sim.mesh)

                # TODO Parse workers to simulations
                local_sim.workers = self.params.distributed_workers
                local_data = data.Data(survey)

                if self.params.forward_only:
                    lmisfit = data_misfit.L2DataMisfit(
                        local_data, local_sim, model_map=local_map
                    )

                else:
                    local_data.dobs = survey.dobs
                    local_data.standard_deviation = survey.std
                    lmisfit = data_misfit.L2DataMisfit(
                        data=local_data,
                        simulation=local_sim,
                        model_map=local_map,
                    )
                    lmisfit.W = 1 / survey.std
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
