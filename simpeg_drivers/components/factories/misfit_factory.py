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

import os
import pickle
from typing import TYPE_CHECKING

import numpy as np
from dask.distributed import wait
from simpeg import objective_function
from simpeg.dask import objective_function as dask_objective_function
from simpeg.objective_function import ComboObjectiveFunction

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.utils.nested import create_misfit


if TYPE_CHECKING:
    from simpeg_drivers.options import BaseOptions


class MisfitFactory(SimPEGFactory):
    """Build SimPEG global misfit function."""

    def __init__(self, params, client, simulation, workers):
        """
        :param params: Options object containing SimPEG object parameters.
        """
        super().__init__(params)

        self.simpeg_object = self.concrete_object()
        self.factory_type = self.params.inversion_type
        self.simulation = simulation
        self.client = client
        self.workers = workers

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

        use_futures = self.client

        # Pickle the simulation to the temporary file
        with open(
            self.params.workpath / (self.params.geoh5.h5file.stem + ".pkl"), mode="wb"
        ) as temp_file:
            pickle.dump(self.simulation, temp_file)

        misfits = []
        tile_count = 0
        for channel in channels:
            for local_indices in tiles:
                for sub_ind in local_indices:
                    if len(sub_ind) == 0:
                        continue

                    args = (
                        sub_ind,
                        temp_file.name,
                        channel,
                        tile_count,
                        self.params.padding_cells,
                        self.params.forward_only,
                        np.hstack(local_indices),
                    )
                    # Distribute the work across workers round-robin style
                    if use_futures:
                        worker_ind = tile_count % len(self.workers)

                        misfits.append(
                            self.client.submit(
                                create_misfit,
                                *args,
                                workers=self.workers[worker_ind],
                            )
                        )

                    else:
                        misfits.append(create_misfit(*args))

                    name = f"{self.params.inversion_type}: Tile {tile_count + 1}"
                    if channel is not None:
                        name += f": Channel {channel}"

                    misfits[-1].name = f"{name}"

                    tile_count += 1

                    if use_futures and tile_count % len(self.workers) == 0:
                        wait(misfits)

        os.unlink(temp_file.name)

        local_orderings = self.collect_ordering_from_misfits(misfits)
        self.simulation.survey.ordering = np.vstack(local_orderings)

        return misfits

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""

    def build(self, tiles, **_):
        """To be over-ridden in factory implementations."""

        misfits = self.assemble_arguments(tiles)

        if self.client:
            return dask_objective_function.DistributedComboMisfits(
                misfits,
                client=self.client,
                workers=self.workers,
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
        for misfit in misfits:
            if self.client:
                attributes.append(
                    self.client.submit(
                        _get_ordering,
                        misfit,
                        workers=self.client.who_has(misfit)[misfit.key],
                    )
                )
            else:
                attributes += _get_ordering(misfit)

        if self.client:
            ordering = []
            for future in self.client.gather(attributes):
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
