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

from simpeg_drivers.electricals.driver import BasePseudo3DDriver
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.constants import (
    validations,
)
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.params import (
    InducedPolarizationPseudo3DForwardParams,
    InducedPolarizationPseudo3DInversionParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions.params import (
    InducedPolarization2DForwardParams,
    InducedPolarization2DInversionParams,
)


class InducedPolarizationPseudo3DForwardDriver(BasePseudo3DDriver):
    _params_class = InducedPolarizationPseudo3DForwardParams
    _params_2d_class = InducedPolarization2DForwardParams
    _validations = validations
    _model_list = ["conductivity_model"]


class InducedPolarizationPseudo3DInversionDriver(BasePseudo3DDriver):
    _params_class = InducedPolarizationPseudo3DInversionParams
    _params_2d_class = InducedPolarization2DInversionParams
    _validations = validations
    _model_list = ["conductivity_model"]
