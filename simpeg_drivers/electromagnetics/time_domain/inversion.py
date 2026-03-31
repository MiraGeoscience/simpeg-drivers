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

from simpeg_drivers.driver import InversionDriver

from .options import TDEMInversionOptions


class TDEMInversionDriver(InversionDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEMInversionOptions


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    TDEMInversionDriver.start_dask_run(file)
