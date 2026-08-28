# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=W0221

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.locations import azimuth_dip_from_segments
from geoapps_utils.utils.transformations import x_rotation_matrix, z_rotation_matrix
from geoh5py.groups import PropertyGroup
from geoh5py.objects import (
    CurrentElectrode,
    Curve,
    Grid2D,
    LargeLoopGroundFEMTransmitters,
    LargeLoopGroundTEMTransmitters,
    Points,
    PotentialElectrode,
)
from geoh5py.objects.surveys.electromagnetics.base import BaseEMSurvey

from simpeg_drivers.components.factories.abstract_factory import AbstractFactory
from simpeg_drivers.utils.surveys import counter_clockwise_sort


logger = getLogger(__name__)

if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData


class EntityFactory(AbstractFactory):
    def __init__(self, params):
        self.params = params
        super().__init__(params)

    @property
    def factory_type(self):
        """Returns inversion type used to switch concrete objects and build methods."""
        return self.params.inversion_type

    @property
    def concrete_object(self):
        """Returns a geoh5py object to be constructed by the build method."""
        if "current" in self.factory_type or "polarization" in self.factory_type:
            return PotentialElectrode, CurrentElectrode

        elif isinstance(self.params.data_object, Grid2D):
            return Points

        else:
            return type(self.params.data_object)

    def build(self, inversion_data: InversionData):
        """Constructs geoh5py object for provided inversion type."""

        entity = self._build(inversion_data)

        return entity

    def _build(self, inversion_data: InversionData):
        if isinstance(self.params.data_object, Grid2D):
            entity = inversion_data.create_entity(
                "Data", inversion_data.locations, geoh5_object=self.concrete_object
            )

        else:
            kwargs = {
                "parent": self.params.out_group,
                "copy_children": False,
            }
            entity = self.params.data_object.copy(**kwargs)

        if isinstance(self.params.data_object, BaseEMSurvey):
            if isinstance(
                self.params.data_object.transmitters,
                LargeLoopGroundFEMTransmitters | LargeLoopGroundTEMTransmitters,
            ):
                cells = self._validate_large_loop_cells(
                    self.params.data_object.transmitters
                )
                entity.transmitters.cells = cells

            if self.params.data_object.transmitters is not None:
                tx_freq = self.params.data_object.transmitters.get_data("Tx frequency")
                if tx_freq:
                    tx_freq[0].copy(parent=entity.transmitters)

            if "borehole" in self.params.inversion_type:
                if property_group := self.params.receivers_orientation is not None:
                    property_group.copy(parent=entity)
                else:
                    self._add_auv_data_groups(entity)

        return entity

    @staticmethod
    def _add_auv_data_groups(entity: Curve):
        """
        Compute the segments orientation and add A, U and V vector data
        to the entity.

        :param entity: Curve entity
        """
        azi_dip = azimuth_dip_from_segments(entity, reverse=True)

        for ind, comp in enumerate("vau"):
            vector = np.zeros((azi_dip.shape[0], 3))
            vector[:, ind] = 1
            vector = (
                z_rotation_matrix(-azi_dip[:, 0])
                * (x_rotation_matrix(-azi_dip[:, 1]) * vector.flatten())
            ).reshape((-1, 3))
            vec_data = entity.add_data(
                {
                    f"{comp}_x": {"values": vector[:, 0]},
                    f"{comp}_y": {"values": vector[:, 1]},
                    f"{comp}_z": {"values": vector[:, 2]},
                }
            )
            PropertyGroup(
                entity,
                property_group_type="3D vector",
                name=f"{comp}_ori".capitalize(),
                properties=vec_data,
            )

    @staticmethod
    def _prune_from_indices(curve: Curve, cell_indices: np.ndarray):
        cells = curve.cells[cell_indices]
        uni_ids, ids = np.unique(cells, return_inverse=True)
        locations = curve.vertices[uni_ids, :]
        cells = np.arange(uni_ids.shape[0], dtype="uint32")[ids].reshape((-1, 2))
        return locations, cells

    @staticmethod
    def _validate_large_loop_cells(
        transmitter: LargeLoopGroundFEMTransmitters | LargeLoopGroundTEMTransmitters,
    ) -> np.ndarray:
        """
        Validate that the transmitter loops are counter-clockwise sorted and closed.
        """
        if transmitter.receivers.tx_id_property is None:
            raise GeoAppsError(
                "Transmitter ID property required for LargeLoopGroundTEMReceivers"
            )

        tx_rx = transmitter.receivers.tx_id_property.values
        tx_ids = transmitter.tx_id_property.values

        all_loops = []
        for tx_id in np.unique(tx_rx):
            messages = []

            tx_ind = tx_ids == tx_id
            loop_cells = transmitter.cells[np.all(tx_ind[transmitter.cells], axis=1), :]

            ccw_loops = counter_clockwise_sort(loop_cells, transmitter.vertices)

            if not np.all(ccw_loops == loop_cells):
                messages.append("'counter-clockwise sorting'")

            # Check for closed loop
            if ccw_loops[-1, 1] != ccw_loops[0, 0]:
                messages.append("'closed loop'")
                ccw_loops = np.vstack(
                    [ccw_loops, np.c_[ccw_loops[-1, 1], ccw_loops[0, 0]]]
                )

            if len(messages) > 0:
                logger.info("Loop %i modified for: %s", tx_id, ", ".join(messages))

            all_loops.append(ccw_loops)

        return np.vstack(all_loops)
