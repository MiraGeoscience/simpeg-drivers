#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from simpeg_drivers.components.locations import InversionLocations


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
