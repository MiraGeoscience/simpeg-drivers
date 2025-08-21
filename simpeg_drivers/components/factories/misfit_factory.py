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
from typing import TYPE_CHECKING

import numpy as np
from dask import compute, delayed
from simpeg import objective_function

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.utils.nested import create_misfit


if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver
    from simpeg_drivers.options import BaseOptions


class MisfitFactory(SimPEGFactory):
    """Build SimPEG global misfit function."""

    def __init__(self, driver: InversionDriver):
        """
        :param params: Options object containing SimPEG object parameters.
        """
        super().__init__(driver.params)
        self.driver = driver
        self.simpeg_object = self.concrete_object()
        self.factory_type = self.params.inversion_type
        self.simulation = driver.simulation

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
        delayed_creation = delayed(create_misfit)

        count = 0
        tile_count = 0
        for channel in channels:
            for local_indices in tiles:
                if len(local_indices) == 0:
                    continue

                for split_ind in np.array_split(local_indices, split_list[count]):
                    futures.append(
                        delayed_creation(
                            self.simulation,
                            split_ind,
                            channel,
                            tile_count,
                            self.params.padding_cells,
                            self.params.inversion_type,
                            self.params.forward_only,
                            shared_indices=local_indices,
                        )
                    )
                    tile_count += 1
                count += 1

        local_misfits = []
        local_orderings = []
        for misfit, ordering in compute(futures)[0]:
            local_misfits.append(misfit)
            local_orderings.append(ordering)

        self.simulation.survey.ordering = np.vstack(local_orderings)
        return [local_misfits]

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""
        return {}
