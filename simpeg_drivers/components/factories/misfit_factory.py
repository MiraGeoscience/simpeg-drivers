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
        if self.factory_type in ["magnetotellurics", "tipper", "fdem", "fdem 1d"]:
            channels = self.simulation.survey.frequencies
        else:
            channels = [None]

        futures = []
        tile_count = 0
        data_count = 0
        misfit_count = 0

        # TODO bring back on GEOPY-2182
        # with ProcessPoolExecutor() as executor:
        for local_index in tiles:
            if len(local_index) == 0:
                continue

            n_split = split_list[misfit_count : misfit_count + len(channels)]
            futures.append(
                # executor.submit(
                create_misfit(
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
            tile_count += np.sum(n_split)

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
