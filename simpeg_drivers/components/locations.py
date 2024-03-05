#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved


from __future__ import annotations

import numpy as np
from geoh5py.data import NumericData
from geoh5py.objects import ObjectBase
from geoh5py.objects.surveys.direct_current import BaseElectrode


class InversionLocations:
    """
    Retrieve topography data from workspace and apply transformations.

    Attributes
    ----------
    mask :
        Mask that stores cumulative filtering actions.
    locations :
        xyz locations.

    Methods
    -------
    get_locations() :
        Returns locations of data object centroids or vertices.
    filter() :
        Apply accumulated self.mask to array, or dict of arrays.

    """

    def __init__(
        self, entity: ObjectBase, elevations: NumericData | float | None = None
    ):
        """
        :param entity: Inversion driver object.
        :param elevations: Optional elevation data.
        """
        self._entity = entity
        self._elevations = elevations
        self.mask: np.ndarray | None = None
        self.locations: np.ndarray = self.compute_locations()

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, v):
        if v is None:
            self._mask = v
            return
        if np.all([n in [0, 1] for n in np.unique(v)]):
            v = np.array(v, dtype=bool)
        else:
            raise ValueError(f"Badly formed mask array {v}")
        self._mask = v

    def get_locations(self):
        """
        Returns entity's centroids or vertices.

        :return: Array shape(*, 3) of x, y, z location data

        """
        if hasattr(self._entity, "centroids"):
            locations = self._entity.centroids
        elif hasattr(self._entity, "vertices"):
            if isinstance(self._entity, BaseElectrode):
                potentials = self._entity.potential_electrodes
                locations = np.mean(
                    [
                        potentials.vertices[potentials.cells[:, 0], :],
                        potentials.vertices[potentials.cells[:, 1], :],
                    ],
                    axis=0,
                )
            else:
                locations = self._entity.vertices

        else:
            raise ValueError(
                f"Workspace object {self._entity} 'vertices' attribute is None."
                " Object type should be Grid2D or point-like."
            )

        return locations

    def _filter(self, a, mask):
        for k, v in a.items():
            if not isinstance(v, np.ndarray):
                a.update({k: self._filter(v, mask)})
            else:
                a.update({k: v[mask]})
        return a

    def _none_dict(self, a):
        is_none = []
        for v in a.values():
            if isinstance(v, dict):
                v = None if self._none_dict(v) else 1
            is_none.append(v is None)
        return all(is_none)

    def filter(self, a: dict[str, np.ndarray] | np.ndarray, mask=None):
        """
        Apply accumulated self.mask to array, or dict of arrays.

        If argument a is a dictionary filter will be applied to all key/values.

        :param a: Object containing data to filter.

        :return: Filtered data.

        """

        mask = self.mask if mask is None else mask

        if isinstance(a, dict):
            if self._none_dict(a):
                return a
            return self._filter(a, mask)

        if a is None:
            return None
        return a[mask]

    def compute_locations(self) -> np.ndarray:
        """
        Returns locations of data object centroids or vertices.

        :param obj: geoh5py object containing centroid or
            vertex location data

        :return: Array shape(*, 3) of x, y, z location data

        """

        locs = self.get_locations()

        if self._elevations is not None:
            if isinstance(self._elevations, NumericData):
                elev = self._elevations.values
            else:
                elev = np.ones_like(locs[:, 2]) * self._elevations

            locs[:, 2] = elev

        return locs
