#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

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
