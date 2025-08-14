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

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.options import (
    DCBatch2DForwardOptions,
    DCBatch2DInversionOptions,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.options import (
    DC2DForwardOptions,
    DC2DInversionOptions,
)
from simpeg_drivers.electricals.driver import BaseBatch2DDriver


class DCBatch2DForwardDriver(BaseBatch2DDriver):
    """Direct Current batch 2D forward driver."""

    _options_class = DCBatch2DForwardOptions
    _params_2d_class = DC2DForwardOptions
    _validations = None


class DCBatch2DInversionDriver(BaseBatch2DDriver):
    """Direct Current batch 2D inversion driver."""

    _options_class = DCBatch2DInversionOptions
    _params_2d_class = DC2DInversionOptions
    _validations = None
