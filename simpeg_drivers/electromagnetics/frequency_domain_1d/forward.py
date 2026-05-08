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
from simpeg_drivers.electromagnetics.base_1d_driver import Base1DDriver
from simpeg_drivers.electromagnetics.frequency_domain_1d.options import (
    FDEM1DForwardOptions,
)


class FDEM1DForwardDriver(ForwardDriver, Base1DDriver):
    """Frequency Domain 1D Electromagnetic forward driver."""

    _params_class = FDEM1DForwardOptions


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    FDEM1DForwardDriver.start_dask_run(file)
