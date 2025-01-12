# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part simpeg-drivers package.                                        '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


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
