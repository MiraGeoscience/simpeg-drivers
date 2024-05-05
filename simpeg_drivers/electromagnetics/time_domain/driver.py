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

import numpy as np
from geoh5py.objects.surveys.electromagnetics.ground_tem import (
    LargeLoopGroundTEMReceivers,
)

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.utils import tile_locations

from .constants import validations
from .params import TimeDomainElectromagneticsParams


class TimeDomainElectromagneticsDriver(InversionDriver):
    _params_class = TimeDomainElectromagneticsParams
    _validations = validations

    def __init__(self, params: TimeDomainElectromagneticsParams):
        super().__init__(params)

    def get_tiles(self):
        """
        Special method to tile the data based on the transmitters center locations.
        """
        if isinstance(self.params.data_object, LargeLoopGroundTEMReceivers):

            tx_ids = self.params.data_object.transmitters.tx_id_property.values

            uids = np.unique(tx_ids)

            n_groups = np.min([len(uids), self.params.tile_spatial])
            locations = []
            for uid in uids:
                locations.append(
                    np.mean(
                        self.params.data_object.transmitters.vertices[tx_ids == uid],
                        axis=0,
                    )
                )

            tx_tiles = tile_locations(
                np.vstack(locations),
                n_groups,
                method="kmeans",
            )
            rx_ids = self.params.data_object.tx_id_property.values
            tiles = []
            counter = {}
            for t_id, group in enumerate(tx_tiles):
                sub_group = []
                for value in group:
                    receiver_ind = rx_ids == value
                    sub_group.append(np.where(receiver_ind)[0])
                    counter[t_id] = counter.get(t_id, 0) + np.sum(receiver_ind)

                tiles.append(np.hstack(sub_group))

        else:
            locations = self.inversion_data.locations
            tiles = tile_locations(
                locations,
                self.params.tile_spatial,
                method="kmeans",
            )

        return tiles
