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

from .options import TipperForwardOptions, TipperInversionOptions


class TipperForwardDriver(InversionDriver):
    """Tipper forward driver."""

    _params_class = TipperForwardOptions


class TipperInversionDriver(InversionDriver):
    """Tipper inversion driver."""

    _params_class = TipperInversionOptions
