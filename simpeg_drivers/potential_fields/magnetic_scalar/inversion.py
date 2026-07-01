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
from simpeg_drivers.potential_fields.magnetic_scalar.options import (
    MagneticInversionOptions,
)
from simpeg_drivers.utils.utils import argument_parser


class MagneticInversionDriver(InversionDriver):
    """Magnetic susceptibility inversion driver."""

    _params_class = MagneticInversionOptions


if __name__ == "__main__":
    file, args = argument_parser()
    MagneticInversionDriver.start_dask_run(file, **args)
