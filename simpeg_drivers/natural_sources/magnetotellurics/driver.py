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

from .options import MTForwardOptions, MTInversionOptions


class MTForwardDriver(InversionDriver):
    """Magnetotellurics forward driver."""

    _options_class = MTForwardOptions
    _validations = None


class MTInversionDriver(InversionDriver):
    """Magnetotellurics inversion driver."""

    _options_class = MTInversionOptions
    _validations = None
