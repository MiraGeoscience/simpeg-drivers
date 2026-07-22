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

import sys
from pathlib import Path

from simpeg_drivers.driver import ForwardDriver
from simpeg_drivers.electricals.base_2d import Base2DDriver
from simpeg_drivers.electricals.direct_current.two_dimensions.options import (
    DC2DForwardOptions,
)


class DC2DForwardDriver(ForwardDriver, Base2DDriver):
    """Direct Current 2D forward driver."""

    _params_class = DC2DForwardOptions


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    DC2DForwardDriver.start_dask_run(file)
