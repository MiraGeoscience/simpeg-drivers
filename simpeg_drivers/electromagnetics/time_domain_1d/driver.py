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

from simpeg_drivers.electromagnetics.base_1d_driver import Base1DDriver

from .options import (
    TDEM1DForwardOptions,
    TDEM1DInversionOptions,
)


class TDEM1DForwardDriver(Base1DDriver):
    """Time Domain 1D Electromagnetic forward driver."""

    _options_class = TDEM1DForwardOptions
    _validations = None


class TDEM1DInversionDriver(Base1DDriver):
    """Time Domain 1D Electromagnetic inversion driver."""

    _options_class = TDEM1DInversionOptions
    _validations = None
