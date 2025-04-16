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

from .options import DC3DForwardOptions, DC3DInversionOptions


class DC3DForwardDriver(InversionDriver):
    """Direct Current 3D forward driver."""

    _options_class = DC3DForwardOptions
    _validation = None


class DC3DInversionDriver(InversionDriver):
    """Direct Current 3D inversion driver."""

    _options_class = DC3DInversionOptions
    _validation = None
