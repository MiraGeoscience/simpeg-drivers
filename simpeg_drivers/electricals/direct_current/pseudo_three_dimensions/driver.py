#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.constants import (
    validations,
)
from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.params import (
    DirectCurrentPseudo3DParams,
)
from simpeg_drivers.electricals.direct_current.two_dimensions.params import (
    DirectCurrent2DParams,
)
from simpeg_drivers.electricals.driver import BasePseudo3DDriver


class DirectCurrentPseudo3DDriver(BasePseudo3DDriver):
    _params_class = DirectCurrentPseudo3DParams
    _params_2d_class = DirectCurrent2DParams
    _validations = validations
