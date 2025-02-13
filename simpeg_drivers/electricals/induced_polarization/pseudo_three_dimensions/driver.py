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
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.params import (
    IPBatch2DForwardParams,
    IPBatch2DInversionParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.params import (
    IP2DForwardParams,
    IP2DInversionParams,
)


class IPBatch2DForwardDriver(BaseBatch2DDriver):
    """Induced Polarization batch 2D forward driver."""

    _params_class = IPBatch2DForwardParams
    _params_2d_class = IP2DForwardParams
    _validations = {}
    _model_list = ["conductivity_model"]


class IPBatch2DInversionDriver(BaseBatch2DDriver):
    """Induced Polarization batch 2D inversion driver."""

    _params_class = IPBatch2DInversionParams
    _params_2d_class = IP2DInversionParams
    _validations = {}
    _model_list = ["conductivity_model"]
