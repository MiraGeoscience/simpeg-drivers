#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from geoh5py.workspace import Workspace
    from geoapps_utils.driver.params import BaseParams
    from simpeg_drivers.components.meshes import InversionMesh

import warnings

import numpy as np
from geoh5py.shared import Entity

from geoapps_utils.numerical import active_from_xyz, filter_xy
from simpeg_drivers.components.data import InversionData
from simpeg_drivers.components.locations import InversionLocations
from simpeg_drivers.utils.utils import floating_active
from simpeg_drivers.components.utils import get_containing_cells


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
        params: BaseParams,
    ):
        """
        :param: workspace: :obj`geoh5py.workspace.Workspace` object containing location based data.
        :param: params: Params object containing location based data parameters.
        """
        super().__init__(workspace, params)
        self.locations: np.ndarray | None = None
        self.mask: np.ndarray | None = None
        self._initialize()

    def _initialize(self):
        self.locations = self.get_locations(self.params.topography_object)
        self.mask = filter_xy(
            self.locations[:, 0],
            self.locations[:, 1],
            angle=self.angle,
        )

        self.locations = super().filter(self.locations)

        if self.is_rotated:
            self.locations = super().rotate(self.locations)

    def active_cells(self, mesh: InversionMesh, data: InversionData) -> np.ndarray:
        """
        Return mask that restricts models to set of earth cells.

        :param: mesh: inversion mesh.
        :return: active_cells: Mask that restricts a model to the set of
            earth cells that are active in the inversion (beneath topography).
        """
        forced_to_surface = [
            "magnetotellurics",
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
        ]
        if self.params.inversion_type in forced_to_surface:
            active_cells = active_from_xyz(
                mesh.entity, self.locations, grid_reference="bottom"
            )
            active_cells = active_cells[np.argsort(mesh.permutation)]
            print(
                "Adjusting active cells so that receivers are all within an active cell . . ."
            )
            active_cells[get_containing_cells(mesh.mesh, data)] = True

            if floating_active(mesh.mesh, active_cells):
                warnings.warn(
                    "Active cell adjustment has created a patch of active cells in the air, likely due to a faulty survey location."
                )

        else:
            active_cells = active_from_xyz(
                mesh.entity, self.locations, grid_reference="center"
            )
            active_cells = active_cells[np.argsort(mesh.permutation)]

        return active_cells

    def get_locations(self, obj: Entity) -> np.ndarray:
        """
        Returns locations of data object centroids or vertices.

        :param obj: geoh5py object containing centroid or
            vertex location data

        :return: Array shape(*, 3) of x, y, z location data

        """

        locs = super().get_locations(obj)

        if self.params.topography is not None:
            if isinstance(self.params.topography, Entity):
                elev = self.params.topography.values
            elif isinstance(self.params.topography, (int, float)):
                elev = np.ones_like(locs[:, 2]) * self.params.topography
            else:
                elev = self.params.topography.values  # Must be FloatData at this point

            if not np.all(locs[:, 2] == elev):
                locs[:, 2] = elev

        return locs