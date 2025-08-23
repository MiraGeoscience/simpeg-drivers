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

from time import time
from typing import TYPE_CHECKING

import numpy as np
from dask import compute, delayed
from dask.diagnostics import ProgressBar
from simpeg import objective_function
from simpeg.dask import objective_function as dask_objective_function

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.utils.nested import create_misfit, slice_from_ordering


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

    def assemble_arguments(  # pylint: disable=arguments-differ
        self, tiles
    ):
        # Base slice over frequencies
        if self.factory_type in ["magnetotellurics", "tipper", "fdem"]:
            channels = self.simulation.survey.frequencies
        else:
            channels = [None]

        futures = []

        use_futures = (
            self.driver.client
        )  # and not isinstance(self.driver.simulation, BaseEM1DSimulation)

        if use_futures:
            delayed_simulation = self.driver.client.scatter(self.driver.simulation)
        else:
            delayed_simulation = self.simulation
            delayed_creation = delayed(create_misfit)

        tile_count = 0
        ct = time()
        local_orderings = []
        for channel in channels:
            for local_indices in tiles:
                for sub_ind in local_indices:
                    if len(sub_ind) == 0:
                        continue

                    ordering_slice = slice_from_ordering(
                        self.simulation.survey, sub_ind, channel=channel
                    )

                    local_orderings.append(
                        self.simulation.survey.ordering[ordering_slice, :]
                    )

                    # Distribute the work across workers round-robin style
                    if use_futures:
                        worker_ind = tile_count % len(self.driver.workers)
                        futures.append(
                            self.driver.client.submit(
                                create_misfit,
                                delayed_simulation,
                                sub_ind,
                                channel,
                                tile_count,
                                self.params.padding_cells,
                                self.params.inversion_type,
                                self.params.forward_only,
                                shared_indices=np.hstack(local_indices),
                                workers=self.driver.workers[worker_ind],
                            )
                        )
                    else:
                        futures.append(
                            delayed_creation(
                                delayed_simulation,
                                sub_ind,
                                channel,
                                tile_count,
                                self.params.padding_cells,
                                self.params.inversion_type,
                                self.params.forward_only,
                                shared_indices=np.hstack(local_indices),
                            )
                        )
                    tile_count += 1

        self.simulation.survey.ordering = np.vstack(local_orderings)

        if use_futures:
            print(f"Assembled misfit in {time() - ct:.1f} seconds")

            return futures

        with ProgressBar():
            vals = compute(futures)[0]

            print(f"Assembled misfit in {time() - ct:.1f} seconds")

            return vals

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""

    def build(self, tiles, **_):
        """To be over-ridden in factory implementations."""

        misfits = self.assemble_arguments(tiles)

        if self.driver.client:
            return dask_objective_function.DistributedComboMisfits(
                misfits,
                client=self.driver.client,
            )

        return self.simpeg_object(  # pylint: disable=not-callable
            misfits
        )
