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

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.constants import (
    validations,
)
from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.params import (
    DirectCurrentPseudo3DParams,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.params import (
    DirectCurrent2DForwardParams,
    DirectCurrent2DInversionParams,
)
from simpeg_drivers.electricals.driver import BasePseudo3DDriver


class DirectCurrentPseudo3DForwardDriver(BasePseudo3DDriver):
    _params_class = DirectCurrentPseudo3DParams
    _params_2d_class = DirectCurrent2DForwardParams
    _validations = validations


class DirectCurrentPseudo3DDriver(BasePseudo3DDriver):
    _params_class = DirectCurrentPseudo3DParams
    _params_2d_class = DirectCurrent2DInversionParams
    _validations = validations
