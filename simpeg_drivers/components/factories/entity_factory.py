#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from geoh5py.objects import Grid2D, Points, PotentialElectrode

if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData


class EntityFactory:
    def __init__(self, params):
        self.params = params

    @property
    def factory_type(self):
        """Returns inversion type used to switch concrete objects and build methods."""
        return self.params.inversion_type

    @property
    def concrete_object(self):
        """Returns a geoh5py object to be constructed by the build method."""
        if isinstance(self.params.data_object, Grid2D):
            return Points

        return type(self.params.data_object)

    def build(self, inversion_data: InversionData):
        """Constructs geoh5py object for provided inversion type."""
        if isinstance(self.params.data_object, Grid2D):
            entity = inversion_data.create_entity(
                "Data", inversion_data.locations, geoh5_object=self.concrete_object
            )

        else:
            kwargs = {
                "parent": self.params.out_group,
                "copy_children": False,
            }

            if inversion_data.mask is not None and np.any(~inversion_data.mask):
                if (
                    isinstance(self.params.data_object, PotentialElectrode)
                    and self.params.data_object.cells is not None
                ):
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
