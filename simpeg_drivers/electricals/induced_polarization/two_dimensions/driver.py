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

from simpeg_drivers.electricals.base_2d import Base2DDriver, DeprecatedBatch2DDriver

from .options import (
    IP2DForwardOptions,
    IP2DInversionOptions,
)


class IPBatch2DForwardDriver(DeprecatedBatch2DDriver):
    """Deprecated - Direct Current Batch Direct Current 2D forward driver."""

    _params_class = IP2DForwardOptions


class IPBatch2DInversionDriver(DeprecatedBatch2DDriver):
    """Deprecated - Direct Current Batch 2D inversion driver."""

    _params_class = IP2DInversionOptions


class IP2DForwardDriver(Base2DDriver):
    """Induced Polarization 2D forward driver."""

    _params_class = IP2DForwardOptions


class IP2DInversionDriver(Base2DDriver):
    """Induced Polarization 2D inversion driver."""

    _params_class = IP2DInversionOptions
