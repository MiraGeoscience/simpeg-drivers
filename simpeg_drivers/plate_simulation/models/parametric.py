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

from abc import ABC, abstractmethod

import numpy as np
from geoh5py.objects import Octree, Surface
from trimesh import Trimesh
from trimesh.proximity import ProximityQuery

from simpeg_drivers.utils.utils import active_from_xyz


class Parametric(ABC):
    """
    Base class representing parametric geometries.
    """

    def __init__(self, surface: Surface):
        if not isinstance(surface, Surface):
            raise TypeError(
                "Input attribute 'surface' should be in instance of geoh5py.Surface."
            )

        self._surface = surface

    @property
    def surface(self):
        """
        Surface object representing the shape of the object.
        """
        return self._surface

    @abstractmethod
    def mask(self, mesh: Octree) -> np.ndarray:
        """
        Return logical for cells inside the parametric object.
        """


class Body(Parametric):
    """
    Represents a closed surface in the model.

    :param surface: geoh5py Surface object representing a closed surface
    """

    def mask(self, mesh: Octree) -> np.ndarray:
        """
        True for cells that lie within the closed surface.

        :param mesh: Octree mesh on which the mask is computed.
        """
        triangulation = Trimesh(
            vertices=self.surface.vertices, faces=self.surface.cells
        )
        proximity_query = ProximityQuery(triangulation)
        dist = proximity_query.signed_distance(mesh.centroids)
        return dist > 0


class Boundary(Parametric):
    """
    Represents a boundary in a model.

    :param surface: geoh5py Surface object representing a boundary
        in the model.
    """

    def vertical_shift(self, offset: float) -> np.ndarray:
        """
        Returns the surface vertices shifted vertically by offset.

        :param offset: Shifts vertices in up (positive) or down (negative).
        """

        if self.surface.vertices is None:
            raise ValueError("Surface vertices are not defined.")

        shift = np.c_[
            np.zeros(self.surface.vertices.shape[0]),
            np.zeros(self.surface.vertices.shape[0]),
            np.ones(self.surface.vertices.shape[0]) * offset,
        ]
        return self.surface.vertices + shift

    def mask(
        self, mesh: Octree, offset: float = 0.0, reference: str = "center"
    ) -> np.ndarray:
        """
        True for cells whose reference lie below the surface.

        :param mesh: Octree mesh on which the mask is computed.
        :param offset: Statically shift the surface on which the mask
            is computed.
        :param reference: Use "bottom", "center" or "top" of the cells
            in determining the mask.

        """

        return active_from_xyz(mesh, self.vertical_shift(offset), reference)
