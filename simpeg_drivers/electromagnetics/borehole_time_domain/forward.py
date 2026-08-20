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

from simpeg_drivers.driver import ForwardDriver
from simpeg_drivers.electromagnetics.borehole_time_domain.options import (
    BoreholeTDEMForwardOptions,
)
from simpeg_drivers.utils.utils import argument_parser


class BoreholeTDEMForwardDriver(ForwardDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = BoreholeTDEMForwardOptions


if __name__ == "__main__":
    # file, args = argument_parser()
    file = r"C:\Users\dominiquef\Documents\tests\Borehole_EM\fwr_model_A.ui.json"
    BoreholeTDEMForwardDriver.start_dask_run(file)
