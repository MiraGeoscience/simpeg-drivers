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

from simpeg_drivers.driver import InversionDriver

from .options import AppConForwardOptions, AppConInversionOptions


class AppConForwardDriver(InversionDriver):
    """AppCon forward driver."""

    _params_class = AppConForwardOptions


class AppConInversionDriver(InversionDriver):
    """AppCon inversion driver."""

    _params_class = AppConInversionOptions
