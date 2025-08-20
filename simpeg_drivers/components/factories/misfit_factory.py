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

from typing import TYPE_CHECKING

import numpy as np
from simpeg import objective_function
from simpeg.simulation import BaseSimulation

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.utils.nested import create_misfit


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

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

    def concrete_object(self):
        return objective_function.ComboObjectiveFunction

    def build(self, tiles, split_list):  # pylint: disable=arguments-differ
        global_misfit = super().build(
            tiles=tiles,
            split_list=split_list,
        )
        return global_misfit

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
        # TODO bring back on GEOPY-2182
        # with ProcessPoolExecutor() as executor:
        count = 0
        for channel in channels:
            tile_count = 0
            for local_indices in tiles:
                if len(local_indices) == 0:
                    continue

                n_split = split_list[count]
                futures.append(
                    # executor.submit(
                    create_misfit(
                        self.simulation,
                        local_indices,
                        channel,
                        tile_count,
                        n_split,
                        self.params.padding_cells,
                        self.params.inversion_type,
                        self.params.forward_only,
                    )
                )
                tile_count += np.sum(n_split)
                count += 1

        local_misfits = []
        local_orderings = []
        for future in futures:  # as_completed(futures):
            misfits, orderings = future  # future.result()
            local_misfits += misfits
            local_orderings += orderings

        self.simulation.survey.ordering = np.vstack(local_orderings)
        return [local_misfits]

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""
        return {}
