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


if TYPE_CHECKING:
    from geoh5py.workspace import Workspace

    from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions

import numpy as np
from geoh5py.objects import ObjectBase, Points
from geoh5py.objects.surveys.direct_current import BaseElectrode
from geoh5py.shared import Entity
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree


class InversionLocations:
    """
    Retrieve topography data from workspace and apply transformations.

    Parameters
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
        self,
        workspace: Workspace,
        params: BaseForwardOptions | BaseInversionOptions,
    ):
        """
        :param workspace: Geoh5py workspace object containing location based data.
        :param params: Options object containing location based data parameters.
        """
        self.workspace = workspace
        self._params: BaseForwardOptions | BaseInversionOptions = params
        self.mask: np.ndarray | None = None
        self.locations: np.ndarray | None = None

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
            msg = f"Badly formed mask array {v}"
            raise (ValueError(msg))
        self._mask = v

    def create_entity(self, name, locs: np.ndarray, geoh5_object=Points):
        """Create Data group and Points object with observed data."""

        entity = geoh5_object.create(
            self.workspace,
            name=name,
            vertices=locs,
            parent=self.params.out_group,
        )

        return entity

    def get_locations(self, entity: ObjectBase) -> np.ndarray:
        """
        Returns entity's centroids or vertices.

        If no location data is found on the provided entity, the method will
        attempt to call itself on its parent.

        :param workspace: Geoh5py Workspace entity.
        :param entity: Object or uuid of entity containing centroid or
            vertex location data.

        :return: Array shape(*, 3) of x, y, z location data

        """
        if hasattr(entity, "vertices"):
            if isinstance(entity, BaseElectrode):
                potentials = entity.potential_electrodes
                locations = np.mean(
                    [
                        potentials.vertices[potentials.cells[:, 0], :],
                        potentials.vertices[potentials.cells[:, 1], :],
                    ],
                    axis=0,
                )
            else:
                locations = entity.vertices
        elif hasattr(entity, "centroids"):
            locations = entity.centroids
        else:
            msg = f"Workspace object {entity} 'vertices' attribute is None."
            msg += " Object type should be Grid2D or point-like."
            raise (ValueError(msg))

        return locations

    def _filter(self, a, mask):
        if a is None:
            return None
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

    def filter(self, obj: dict[str, np.ndarray] | np.ndarray, mask=None):
        """
        Apply accumulated self.mask to array, or dict of arrays.

        If argument a is a dictionary filter will be applied to all key/values.

        :param obj: Object containing data to filter.

        :return: Filtered data.

        """

        mask = self.mask if mask is None else mask

        if isinstance(obj, dict):
            if self._none_dict(obj):
                return obj
            else:
                return self._filter(obj, mask)
        else:
            if obj is None:
                return None
            else:
                return obj[mask]

    @property
    def params(self):
        """Associated parameters."""
        return self._params
