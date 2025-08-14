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
    FDEM1DForwardOptions,
    FDEM1DInversionOptions,
)


class FDEM1DForwardDriver(Base1DDriver):
    """Frequency Domain 1D Electromagnetic forward driver."""

    _options_class = FDEM1DForwardOptions
    _validations = None


class FDEM1DInversionDriver(Base1DDriver):
    """Frequency Domain 1D Electromagnetic inversion driver."""

    _options_class = FDEM1DInversionOptions
    _validations = None
