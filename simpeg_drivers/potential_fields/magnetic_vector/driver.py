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

from simpeg import maps

from simpeg_drivers.driver import InversionDriver

from .options import MVIForwardOptions, MVIInversionOptions


class MVIForwardDriver(InversionDriver):
    """Magnetic Vector forward driver."""

    _params_class = MVIForwardOptions


class MVIInversionDriver(InversionDriver):
    """Magnetic Vector inversion driver."""

    _params_class = MVIInversionOptions
