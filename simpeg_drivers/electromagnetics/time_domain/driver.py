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

import numpy as np
from geoh5py.objects.surveys.electromagnetics.ground_tem import (
    LargeLoopGroundTEMReceivers,
)

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.utils import tile_locations

from .params import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)


class TDEMForwardDriver(InversionDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = TDEMForwardOptions
    _validations = None

    def get_tiles(self) -> list[np.ndarray]:
        """
        Special method to tile the data based on the transmitters center locations.

        First the transmitter locations are grouped into groups using kmeans clustering.
        Second, if the number of groups is less than the number of 'tile_spatial' value, the groups are
        further divided into groups based on the clustering of receiver locations.
        """
        if not isinstance(self.params.data_object, LargeLoopGroundTEMReceivers):
            return super().get_tiles()

        tx_ids = self.params.data_object.transmitters.tx_id_property.values
        unique_tile_ids = np.unique(tx_ids)
        n_groups = np.min([len(unique_tile_ids), self.params.tile_spatial])
        locations = []
        for uid in unique_tile_ids:
            locations.append(
                np.mean(
                    self.params.data_object.transmitters.vertices[tx_ids == uid],
                    axis=0,
                )
            )

        # Tile transmitters spatially by loop center
        tx_tiles = tile_locations(
            np.vstack(locations),
            n_groups,
            method="kmeans",
        )
        receivers_tx_ids = self.params.data_object.tx_id_property.values
        tiles = []
        for _t_id, group in enumerate(tx_tiles):
            sub_group = []
            for value in group:
                receiver_ind = receivers_tx_ids == unique_tile_ids[value]
                sub_group.append(np.where(receiver_ind)[0])

            tiles.append(np.hstack(sub_group))

        # If number of tiles remaining, brake up receivers spatially per transmitter
        while len(tiles) < self.params.tile_spatial:
            largest_group = np.argmax([len(tile) for tile in tiles])
            tile = tiles.pop(largest_group)
            new_tiles = tile_locations(
                self.params.data_object.vertices[tile],
                2,
                method="kmeans",
            )
            tiles += [tile[new_tiles[0]], tile[new_tiles[1]]]

        return tiles


class TDEMInversionDriver(InversionDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEMInversionOptions
    _validations = None

    def get_tiles(self) -> list[np.ndarray]:
        """
        Special method to tile the data based on the transmitters center locations.

        First the transmitter locations are grouped into groups using kmeans clustering.
        Second, if the number of groups is less than the number of 'tile_spatial' value, the groups are
        further divided into groups based on the clustering of receiver locations.
        """
        if not isinstance(self.params.data_object, LargeLoopGroundTEMReceivers):
            return super().get_tiles()

        tx_ids = self.params.data_object.transmitters.tx_id_property.values
        unique_tile_ids = np.unique(tx_ids)
        n_groups = np.min([len(unique_tile_ids), self.params.tile_spatial])
        locations = []
        for uid in unique_tile_ids:
            locations.append(
                np.mean(
                    self.params.data_object.transmitters.vertices[tx_ids == uid],
                    axis=0,
                )
            )

        # Tile transmitters spatially by loop center
        tx_tiles = tile_locations(
            np.vstack(locations),
            n_groups,
            method="kmeans",
        )
        receivers_tx_ids = self.params.data_object.tx_id_property.values
        tiles = []
        for _t_id, group in enumerate(tx_tiles):
            sub_group = []
            for value in group:
                receiver_ind = receivers_tx_ids == unique_tile_ids[value]
                sub_group.append(np.where(receiver_ind)[0])

            tiles.append(np.hstack(sub_group))

        # If number of tiles remaining, brake up receivers spatially per transmitter
        while len(tiles) < self.params.tile_spatial:
            largest_group = np.argmax([len(tile) for tile in tiles])
            tile = tiles.pop(largest_group)
            new_tiles = tile_locations(
                self.params.data_object.vertices[tile],
                2,
                method="kmeans",
            )
            tiles += [tile[new_tiles[0]], tile[new_tiles[1]]]

        return tiles
