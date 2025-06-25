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

from abc import ABC, abstractmethod

import numpy as np
from geoapps_utils.modelling.plates import PlateModel, inside_plate
from geoapps_utils.utils.transformations import (
    rotate_points,
    rotate_xyz,
    x_rotation_matrix,
    z_rotation_matrix,
)
from geoh5py.objects import Octree, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.workspace import Workspace
from trimesh import Trimesh
from trimesh.proximity import ProximityQuery

from simpeg_drivers.plate_simulation.models.options import PlateOptions
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


class Plate(Parametric):
    """
    Define a rotated rectangular block in 3D space

    :param params: Parameters describing the plate.
    :param surface: Surface object representing the plate.
    """

    def __init__(
        self,
        params: PlateOptions,
        center: tuple[float, float, float] = (
            0.0,
            0.0,
            0.0,
        ),
        workspace: Workspace | None = None,
    ):
        self.params = params
        self.center = center
        self._workspace = workspace
        super().__init__(self._create_surface())

    def _create_surface(self) -> Surface:
        """
        Create a surface object from a plate object.

        :param workspace: Workspace object to create the surface in.
        :param out_group: Output group to store the surface.
        """
        with fetch_active_workspace(self.workspace) as ws:
            surface = Surface.create(
                ws,
                vertices=self.vertices,
                cells=self.triangles,
                name=self.params.name,
            )

        return surface

    @property
    def surface(self):
        """
        A surface object representing the plate.
        """
        return self._surface

    @property
    def triangles(self) -> np.ndarray:
        """Triangulation of the block."""
        return np.vstack(
            [
                [0, 2, 1],
                [1, 2, 3],
                [0, 1, 4],
                [4, 1, 5],
                [1, 3, 5],
                [5, 3, 7],
                [2, 6, 3],
                [3, 6, 7],
                [0, 4, 2],
                [2, 4, 6],
                [4, 5, 6],
                [6, 5, 7],
            ]
        )

    @property
    def vertices(self) -> np.ndarray:
        """Vertices for triangulation of a rectangular prism in 3D space."""

        u_1 = self.center[0] - (self.params.strike_length / 2.0)
        u_2 = self.center[0] + (self.params.strike_length / 2.0)
        v_1 = self.center[1] - (self.params.dip_length / 2.0)
        v_2 = self.center[1] + (self.params.dip_length / 2.0)
        w_1 = self.center[2] - (self.params.width / 2.0)
        w_2 = self.center[2] + (self.params.width / 2.0)

        vertices = np.array(
            [
                [u_1, v_1, w_1],
                [u_2, v_1, w_1],
                [u_1, v_2, w_1],
                [u_2, v_2, w_1],
                [u_1, v_1, w_2],
                [u_2, v_1, w_2],
                [u_1, v_2, w_2],
                [u_2, v_2, w_2],
            ]
        )

        return self._rotate(vertices)

    @property
    def workspace(self) -> Workspace:
        if self._workspace is None:
            self._workspace = Workspace()

        return self._workspace

    def _rotate(self, vertices: np.ndarray) -> np.ndarray:
        """Rotate vertices and adjust for reference point."""
        theta = -1 * self.params.dip_direction
        phi = -1 * self.params.dip
        rotated_vertices = rotate_xyz(vertices, self.center, theta, phi)

        return rotated_vertices

    def mask(self, mesh: Octree) -> np.ndarray:
        plate = PlateModel(
            strike_length=self.params.strike_length,
            dip_length=self.params.dip_length,
            width=self.params.width,
            direction=self.params.dip_direction,
            dip=self.params.dip,
            origin=self.center,
        )
        rotations = [
            z_rotation_matrix(np.deg2rad(self.params.dip_direction)),
            x_rotation_matrix(np.deg2rad(self.params.dip)),
        ]
        rotated_centers = rotate_points(
            mesh.centroids, origin=plate.origin, rotations=rotations
        )
        return inside_plate(rotated_centers, plate)


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
