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
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.constants import (
    validations,
)
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.params import (
    IPBatch2DForwardParams,
    IPBatch2DInversionParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.params import (
    InducedPolarization2DForwardParams,
    InducedPolarization2DInversionParams,
)


class IPBatch2DForwardDriver(BaseBatch2DDriver):
    _params_class = IPBatch2DForwardParams
    _params_2d_class = InducedPolarization2DForwardParams
    _validations = {}
    _model_list = ["conductivity_model"]


class IPBatch2DInversionDriver(BaseBatch2DDriver):
    _params_class = IPBatch2DInversionParams
    _params_2d_class = InducedPolarization2DInversionParams
    _validations = {}
    _model_list = ["conductivity_model"]
