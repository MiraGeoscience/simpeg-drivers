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


# pylint: disable=W0221

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData

import numpy as np
from geoh5py.objects import CurrentElectrode, Curve, Grid2D, Points, PotentialElectrode

from simpeg_drivers.components.factories.abstract_factory import AbstractFactory


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

            entity = self.params.data_object.copy(**kwargs)
            entity.vertices = inversion_data.apply_transformations(entity.vertices)

        if getattr(entity, "transmitters", None) is not None:
            entity.transmitters.vertices = inversion_data.apply_transformations(
                entity.transmitters.vertices
            )
            tx_freq = self.params.data_object.transmitters.get_data("Tx frequency")
            if tx_freq:
                tx_freq[0].copy(parent=entity.transmitters)

        if getattr(entity, "current_electrodes", None) is not None:
            entity.current_electrodes.vertices = inversion_data.apply_transformations(
                entity.current_electrodes.vertices
            )

        return entity

    @staticmethod
    def _prune_from_indices(curve: Curve, cell_indices: np.ndarray):
        cells = curve.cells[cell_indices]
        uni_ids, ids = np.unique(cells, return_inverse=True)
        locations = curve.vertices[uni_ids, :]
        cells = np.arange(uni_ids.shape[0], dtype="uint32")[ids].reshape((-1, 2))
        return locations, cells
