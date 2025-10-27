# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
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

from simpeg_drivers.options import CoreOptions


def test_topo_or_active_validation(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as workspace:
        data = {
            "geoh5": workspace,
            "inversion_type": "mvi",
        }
    with pytest.raises(GeoAppsError, match="active_cells: Value error, Must"):
        CoreOptions.build(data)
