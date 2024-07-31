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


from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams
    from geoh5py.workspace import Workspace

import numpy as np
from geoh5py.objects import Grid2D, PotentialElectrode


class InversionWindow:
    """
    Retrieve and store window data from workspace.

    If params contains no window data, the window will initialize with from the
    data extents.

    Attributes
    ----------

    workspace:
        Geoh5py workspace object containing window data.
    params:
        Params object containing window parameters.
    window:
        Center and size defining window for data, topography, etc.

    Methods
    -------

    is_empty():
        Check if window data is empty.

    """

    window_keys = ["center_x", "center_y", "height", "width", "size", "center"]

    def __init__(self, workspace: Workspace, params: BaseParams):
        """
        :param: workspace: Geoh5py workspace object containing window data.
        :param: params: Params object containing window parameters.
        :param: window:
        """
        self.workspace = workspace
        self.params = params
        self._window: dict[str, Any] | None = None

    def is_empty(self) -> bool:
        """Check if window data is empty."""
        if self._window is None:
            return True
        elif (self._window["size"][0] == 0) & (self._window["size"][1] == 0):
            return True
        else:
            center_x_null = True if self._window["center"][0] is None else False
            center_y_null = True if self._window["center"][1] is None else False
            size_x_null = True if self._window["size"][0] is None else False
            size_y_null = True if self._window["size"][1] is None else False
            return center_x_null & center_y_null & size_x_null & size_y_null

    @property
    def window(self):
        """Get params.window data."""
        if self._window is None:
            if self.is_empty():
                data_object = self.params.data_object
                if isinstance(data_object, Grid2D):
                    locs = data_object.centroids
                elif isinstance(data_object, PotentialElectrode):
                    locs = np.vstack(
                        [data_object.vertices, data_object.current_electrodes.vertices]
                    )
                    locs = np.unique(locs, axis=0)
                else:
                    locs = data_object.vertices

                if locs is None:
                    msg = f"Object {data_object} is not Grid2D object and doesn't contain vertices."
                    raise (ValueError(msg))

                min_corner = np.min(locs[:, :2], axis=0)
                max_corner = np.max(locs[:, :2], axis=0)

                size = max_corner - min_corner
                size[size == 0] = np.mean(size)

                self._window = {
                    "center": np.mean([max_corner, min_corner], axis=0),
                    "size": size,
                }
            else:
                self._window = self.params.window
        return self._window

    def __call__(self):
        return self.window
