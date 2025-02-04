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

from .constants import validations
from .params import (
    InducedPolarization2DForwardParams,
    InducedPolarization2DInversionParams,
)


class InducedPolarization2DForwardDriver(Base2DDriver):
    _params_class = InducedPolarization2DForwardParams
    _validations = validations


class InducedPolarization2DInversionDriver(Base2DDriver):
    _params_class = InducedPolarization2DInversionParams
    _validations = validations
