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

from .constants import validations
from .params import (
    InducedPolarization3DForwardParams,
    InducedPolarization3DInversionParams,
)


class InducedPolarization3DForwardDriver(InversionDriver):
    _params_class = InducedPolarization3DForwardParams
    _validations = validations


class InducedPolarization3DInversionDriver(InversionDriver):
    _params_class = InducedPolarization3DInversionParams
    _validations = validations
