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

from simpeg_drivers.electricals.driver import BasePseudo3DDriver
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.constants import (
    validations,
)
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.params import (
    InducedPolarizationPseudo3DParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.params import (
    InducedPolarization2DParams,
)


class InducedPolarizationPseudo3DDriver(BasePseudo3DDriver):
    _params_class = InducedPolarizationPseudo3DParams
    _params_2d_class = InducedPolarization2DParams
    _validations = validations
    _model_list = ["conductivity_model"]
