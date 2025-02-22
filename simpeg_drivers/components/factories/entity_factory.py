# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
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
from geoh5py.objects import (
    CurrentElectrode,
    Curve,
    Grid2D,
    LargeLoopGroundFEMTransmitters,
    LargeLoopGroundTEMTransmitters,
    Points,
    PotentialElectrode,
)

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

            if np.any(~inversion_data.mask):
                if isinstance(self.params.data_object, PotentialElectrode):
                    active_poles = np.zeros(
                        self.params.data_object.n_vertices, dtype=bool
                    )
                    active_poles[
                        self.params.data_object.cells[inversion_data.mask, :].ravel()
                    ] = True
                    kwargs.update(
                        {"mask": active_poles, "cell_mask": inversion_data.mask}
                    )
                else:
                    kwargs.update({"mask": inversion_data.mask})

            entity = self.params.data_object.copy(copy_complement=False, **kwargs)

        if getattr(self.params.data_object, "transmitters", None) is not None:
            cells = self.params.data_object.transmitters.cells

            if getattr(self.params.data_object, "tx_id_property", None) is not None:
                tx_id = self.params.data_object.tx_id_property.copy(parent=entity)
                entity.tx_id_property = tx_id

            if isinstance(
                self.params.data_object.transmitters,
                LargeLoopGroundFEMTransmitters | LargeLoopGroundTEMTransmitters,
            ):
                cells = self._validate_large_loop_cells(
                    self.params.data_object.transmitters
                )

            transmitters = self.params.data_object.transmitters.copy(
                copy_complement=False,
                cells=cells,
                parent=self.params.out_group,
                copy_children=False,
            )

            if (
                getattr(self.params.data_object.transmitters, "tx_id_property", None)
                is not None
            ):
                tx_id = self.params.data_object.transmitters.tx_id_property.copy(
                    parent=transmitters
                )
                transmitters.tx_id_property = tx_id

            entity.transmitters = transmitters

            tx_freq = self.params.data_object.transmitters.get_data("Tx frequency")
            if tx_freq:
                tx_freq[0].copy(parent=entity.transmitters)

        return entity

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
            raise ValueError(
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
