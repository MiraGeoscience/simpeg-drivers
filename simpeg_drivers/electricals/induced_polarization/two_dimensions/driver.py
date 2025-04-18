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

from simpeg_drivers.electricals.driver import Base2DDriver

from .options import (
    IP2DForwardOptions,
    IP2DInversionOptions,
)


class IP2DForwardDriver(Base2DDriver):
    """Induced Polarization 2D forward driver."""

    _options_class = IP2DForwardOptions
    _validations = None


class IP2DInversionDriver(Base2DDriver):
    """Induced Polarization 2D inversion driver."""

    _options_class = IP2DInversionOptions
    _validations = None
