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

from .params import (
    TDEM1DForwardOptions,
    TDEM1DInversionOptions,
)


class TDEM1DForwardDriver(InversionDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = TDEM1DForwardOptions
    _validations = None


class TDEM1DInversionDriver(InversionDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEM1DInversionOptions
    _validations = None
