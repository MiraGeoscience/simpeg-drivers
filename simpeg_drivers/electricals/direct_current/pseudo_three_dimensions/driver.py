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

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.params import (
    DCBatch2DForwardParams,
    DCBatch2DInversionParams,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.params import (
    DirectCurrent2DForwardParams,
    DirectCurrent2DInversionParams,
)
from simpeg_drivers.electricals.driver import BaseBatch2DDriver


class DCBatch2DForwardDriver(BaseBatch2DDriver):
    _params_class = DCBatch2DForwardParams
    _params_2d_class = DirectCurrent2DForwardParams
    _validations = {}


class DCBatch2DInversionDriver(BaseBatch2DDriver):
    _params_class = DCBatch2DInversionParams
    _params_2d_class = DirectCurrent2DInversionParams
    _validations = {}
