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

from .params import DirectCurrent2DForwardParams, DirectCurrent2DInversionParams


class DirectCurrent2DForwardDriver(Base2DDriver):
    """Direct Current 2D forward driver."""

    _params_class = DirectCurrent2DForwardParams
    _validations = {}


class DirectCurrent2DInversionDriver(Base2DDriver):
    """Direct Current 2D inversion driver."""

    _params_class = DirectCurrent2DInversionParams
    _validations = {}
