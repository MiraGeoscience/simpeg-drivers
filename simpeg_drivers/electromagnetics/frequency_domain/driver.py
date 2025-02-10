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
    FrequencyDomainElectromagneticsForwardParams,
    FrequencyDomainElectromagneticsInversionParams,
)


class FrequencyDomainElectromagneticsForwardDriver(InversionDriver):
    _params_class = FrequencyDomainElectromagneticsForwardParams
    _validations = validations

    def __init__(self, params: FrequencyDomainElectromagneticsForwardParams):
        super().__init__(params)


class FrequencyDomainElectromagneticsInversionDriver(InversionDriver):
    _params_class = FrequencyDomainElectromagneticsInversionParams
    _validations = validations
