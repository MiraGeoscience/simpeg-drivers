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
from simpeg_drivers.potential_fields.gravity.options import (
    GravityForwardOptions,
    GravityInversionOptions,
)


class GravityForwardDriver(InversionDriver):
    """Gravity forward driver."""

    _options_class = GravityForwardOptions
    _validations = None


class GravityInversionDriver(InversionDriver):
    """Gravity inversion driver."""

    _options_class = GravityInversionOptions
    _validations = None
