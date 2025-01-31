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
from simpeg_drivers.potential_fields.gravity.constants import validations
from simpeg_drivers.potential_fields.gravity.params import (
    GravityForwardParams,
    GravityInversionParams,
)


class GravityForwardDriver(InversionDriver):
    _params_class = GravityForwardParams
    _validation = validations


class GravityInversionDriver(InversionDriver):
    _params_class = GravityInversionParams
    _validations = validations
