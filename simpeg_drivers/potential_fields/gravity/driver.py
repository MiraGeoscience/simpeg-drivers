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

import sys
import traceback
import warnings

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.potential_fields.gravity.options import (
    GravityForwardOptions,
    GravityInversionOptions,
)


def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    log = file if hasattr(file, "write") else sys.stderr
    traceback.print_stack(file=log)
    log.write(warnings.formatwarning(message, category, filename, lineno, line))


warnings.showwarning = warn_with_traceback


class GravityForwardDriver(InversionDriver):
    """Gravity forward driver."""

    _params_class = GravityForwardOptions
    print("Hello from GravityForwardDriver1111")


class GravityInversionDriver(InversionDriver):
    """Gravity inversion driver."""

    _params_class = GravityInversionOptions
