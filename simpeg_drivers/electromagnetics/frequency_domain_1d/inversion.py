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

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.electromagnetics.base_1d_driver import Base1DDriver
from simpeg_drivers.electromagnetics.frequency_domain_1d.options import (
    FDEM1DInversionOptions,
)
from simpeg_drivers.utils.utils import argument_parser


class FDEM1DInversionDriver(InversionDriver, Base1DDriver):
    """Frequency Domain 1D Electromagnetic inversion driver."""

    _params_class = FDEM1DInversionOptions


if __name__ == "__main__":
    file, args = argument_parser()
    FDEM1DInversionDriver.start_dask_run(file, **args)
