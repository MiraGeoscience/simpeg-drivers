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
    from geoapps_utils.driver.params import BaseParams
    from geoh5py.workspace import Workspace

    from simpeg_drivers.components.meshes import InversionMesh
    from simpeg_drivers.params import BaseOptions

import warnings

import numpy as np
from discretize import TreeMesh
from geoh5py.data import NumericData
from geoh5py.objects.surveys.electromagnetics.base import LargeLoopGroundEMSurvey
from geoh5py.shared import Entity

from simpeg_drivers.components.data import InversionData
from simpeg_drivers.components.locations import InversionLocations
from simpeg_drivers.components.models import InversionModel
from simpeg_drivers.utils.utils import (
    active_from_xyz,
    floating_active,
    get_containing_cells,
    get_neighbouring_cells,
)


class InversionTopography(InversionLocations):
    """
    Retrieve topography data from workspace and apply transformations.

    Parameters
    ----------
    locations :
        Topography locations.
    mask :
        Mask created by windowing operation and applied to locations
        and data on initialization.

    Methods
    -------
    active_cells(mesh) :
        Return mask that restricts models to active (earth) cells.

    """

    def __init__(
        self,
        workspace: Workspace,
        params: BaseParams | BaseOptions,
    ):
        """
        :param: workspace: :obj`geoh5py.workspace.Workspace` object containing location based data.
        :param: params: Options object containing location based data parameters.
        """
        super().__init__(workspace, params)
        self.locations: np.ndarray | None = None

        if self.params.active_cells.topography_object is not None:
            self.locations = self.get_locations(
                self.params.active_cells.topography_object
            )

    def active_cells(self, mesh: InversionMesh, data: InversionData) -> np.ndarray:
        """
        Return mask that restricts models to set of earth cells.

        :param: mesh: inversion mesh.
        :return: active_cells: Mask that restricts a model to the set of
            earth cells that are active in the inversion (beneath topography).
        """
        forced_to_surface: bool = self.params.inversion_type in [
            "magnetotellurics",
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
        ] or isinstance(data.entity, LargeLoopGroundEMSurvey)

        if isinstance(self.params.active_cells.active_model, NumericData):
            active_cells = InversionModel.obj_2_mesh(
                self.params.active_cells.active_model, mesh.entity
            )
        else:
            active_cells = active_from_xyz(
                mesh.entity,
                self.locations,
                grid_reference="bottom" if forced_to_surface else "center",
            )

        active_cells = active_cells[np.argsort(mesh.permutation)].astype(bool)

        if forced_to_surface:
            active_cells = self.expand_actives(active_cells, mesh, data)

            if floating_active(mesh.mesh, active_cells):
                warnings.warn(
                    "Active cell adjustment has created a patch of active cells in the air, "
                    "likely due to a faulty survey location."
                )

        return active_cells

    def get_locations(self, entity: Entity) -> np.ndarray:
        """
        Returns locations of data object centroids or vertices.

        :param entity: geoh5py object containing centroid or
            vertex location data

        :return: Array shape(*, 3) of x, y, z location data

        """

        locs = super().get_locations(entity)

        if self.params.active_cells.topography is not None:
            if isinstance(self.params.active_cells.topography, Entity):
                elev = self.params.active_cells.topography.values
            elif isinstance(self.params.active_cells.topography, int | float):
                elev = np.ones_like(locs[:, 2]) * self.params.active_cells.topography
            else:
                elev = (
                    self.params.active_cells.topography.values
                )  # Must be FloatData at this point

            if not np.all(locs[:, 2] == elev):
                locs[:, 2] = elev

        return locs

    def expand_actives(
        self, active_cells: np.ndarray, mesh: InversionMesh, data: InversionData
    ) -> np.ndarray:
        """
        Expand active cells to ensure receivers are within active cells.

        :param active_cells: Mask that restricts a model to the set of
        :param mesh: Inversion mesh.
        :param data: Inversion data.

        :return: active_cells: Mask that restricts a model to the set of
        """
        containing_cells = get_containing_cells(mesh.mesh, data)
        active_cells[containing_cells] = True

        # Apply extra active cells to ensure connectivity for tree meshes
        if isinstance(mesh.mesh, TreeMesh):
            neighbours = get_neighbouring_cells(mesh.mesh, containing_cells)
            neighbours_xy = np.r_[neighbours[0] + neighbours[1]]

            # Make sure the new actives are connected to the old actives
            new_actives = ~active_cells[neighbours_xy]
            if np.any(new_actives):
                neighbours = get_neighbouring_cells(
                    mesh.mesh, neighbours_xy[new_actives]
                )
                active_cells[np.r_[neighbours[2][0]]] = True  # z-axis neighbours

            active_cells[neighbours_xy] = True  # xy-axis neighbours

        return active_cells
