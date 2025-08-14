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

from simpeg_drivers.electricals.driver import BaseBatch2DDriver
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.options import (
    IPBatch2DForwardOptions,
    IPBatch2DInversionOptions,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.options import (
    IP2DForwardOptions,
    IP2DInversionOptions,
)


class IPBatch2DForwardDriver(BaseBatch2DDriver):
    """Induced Polarization batch 2D forward driver."""

    _options_class = IPBatch2DForwardOptions
    _params_2d_class = IP2DForwardOptions
    _validations = None
    _model_list = ["conductivity_model"]


class IPBatch2DInversionDriver(BaseBatch2DDriver):
    """Induced Polarization batch 2D inversion driver."""

    _options_class = IPBatch2DInversionOptions
    _params_2d_class = IP2DInversionOptions
    _validations = None
    _model_list = ["conductivity_model"]
