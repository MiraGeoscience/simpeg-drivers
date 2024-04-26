# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


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
