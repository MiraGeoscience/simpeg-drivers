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
from dask import compute, delayed
from dask.diagnostics import ProgressBar
from simpeg import objective_function
from simpeg.dask import objective_function as dask_objective_function
from simpeg.objective_function import ComboObjectiveFunction

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

        use_futures = (
            self.driver.client
        )  # and not isinstance(self.driver.simulation, BaseEM1DSimulation)

        if use_futures:
            delayed_simulation = self.driver.client.scatter(self.driver.simulation)
        else:
            delayed_simulation = self.simulation

        misfits = []
        tile_count = 0
        for channel in channels:
            for local_indices in tiles:
                for sub_ind in local_indices:
                    if len(sub_ind) == 0:
                        continue

                    # Distribute the work across workers round-robin style
                    if use_futures:
                        worker_ind = tile_count % len(self.driver.workers)
                        misfits.append(
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
                        misfits.append(
                            create_misfit(
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

        local_orderings = self.collect_ordering_from_misfits(misfits)

        self.simulation.survey.ordering = np.vstack(local_orderings)

        return misfits

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

    def collect_ordering_from_misfits(self, misfits):
        """Collect attributes from misfit objects.

        :param misfits : List of misfit objects.
        :param attribute :  Attribute to collect.

        :return: List of collected attributes.
        """
        attributes = []
        for ii, misfit in enumerate(misfits):
            if self.driver.client:
                worker_ind = ii % len(self.driver.workers)
                attributes.append(
                    self.driver.client.submit(
                        _get_ordering, misfit, workers=self.driver.workers[worker_ind]
                    )
                )
            else:
                attributes += _get_ordering(misfit)

        if self.driver.client:
            ordering = []
            for future in self.driver.client.gather(attributes):
                ordering += future
            return ordering
        return attributes


def _get_ordering(obj):
    """Recursively get ordering from components of misfit function."""
    attributes = []
    if isinstance(obj, ComboObjectiveFunction):
        for misfit in obj.objfcts:
            attributes += _get_ordering(misfit)

        return attributes
    return [obj.simulation.simulations[0].survey.ordering]
