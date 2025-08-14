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

from .options import DC2DForwardOptions, DC2DInversionOptions


class DC2DForwardDriver(Base2DDriver):
    """Direct Current 2D forward driver."""

    _options_class = DC2DForwardOptions
    _validations = None


class DC2DInversionDriver(Base2DDriver):
    """Direct Current 2D inversion driver."""

    _options_class = DC2DInversionOptions
    _validations = None
