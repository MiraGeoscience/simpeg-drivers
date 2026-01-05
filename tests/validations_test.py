# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import pytest
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py import Workspace
from geoh5py.objects import Grid2D

from simpeg_drivers.options import CoreOptions


def test_topo_or_active_validation(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as workspace:
        data = {
            "geoh5": workspace,
            "inversion_type": "mvi",
        }
    with pytest.raises(GeoAppsError, match="active_cells: Value error, Must"):
        CoreOptions.build(data)


def test_topo_grid_missing_elevation(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as workspace:
        grid = Grid2D.create(
            workspace,
            name="grid",
            u_cell_size=10,
            v_cell_size=10,
            u_count=10,
            v_count=10,
            origin=[0, 0, 0],
        )

        data = {
            "geoh5": workspace,
            "inversion_type": "mvi",
            "topography_object": grid,
            "topography": None,
        }
    with pytest.raises(GeoAppsError, match="active_cells: Value error, Grid2D"):
        CoreOptions.build(data)
