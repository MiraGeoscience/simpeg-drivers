# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
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
    MagneticForwardOptions,
    MagneticInversionOptions,
)


class MagneticForwardDriver(InversionDriver):
    """Magnetic forward driver."""

    _options_class = MagneticForwardOptions
    _validations = None


class MagneticInversionDriver(InversionDriver):
    """Magnetic inversion driver."""

    _options_class = MagneticInversionOptions
    _validations = None
