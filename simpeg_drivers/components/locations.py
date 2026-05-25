# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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
from scipy.spatial import cKDTree


class InversionLocations:
    """
    Retrieve topography data from workspace and apply transformations.

    Parameters
    ----------
    locations :
        xyz locations.

    Methods
    -------
    get_locations() :
        Returns locations of data object centroids or vertices.
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
        self.locations: np.ndarray | None = None

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

    @property
    def params(self):
        """Associated parameters."""
        return self._params
