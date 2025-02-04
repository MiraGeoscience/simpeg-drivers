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
from simpeg_drivers.potential_fields.magnetic_scalar.constants import validations
from simpeg_drivers.potential_fields.magnetic_scalar.params import (
    MagneticScalarForwardParams,
    MagneticScalarInversionParams,
)


class MagneticScalarForwardDriver(InversionDriver):
    _params_class = MagneticScalarForwardParams
    _validations = validations


class MagneticScalarInversionDriver(InversionDriver):
    _params_class = MagneticScalarInversionParams
    _validations = validations
