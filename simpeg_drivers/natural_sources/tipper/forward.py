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
from simpeg_drivers.natural_sources.tipper.options import TipperForwardOptions


class TipperForwardDriver(ForwardDriver):
    """Tipper forward driver."""

    _params_class = TipperForwardOptions


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    TipperForwardDriver.start_dask_run(file)
