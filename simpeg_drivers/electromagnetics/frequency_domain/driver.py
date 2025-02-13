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

from .params import (
    FDEMForwardParams,
    FDEMInversionParams,
)


class FDEMForwardDriver(InversionDriver):
    """Frequency Domain Electromagnetic forward driver."""

    _params_class = FDEMForwardParams
    _validations = {}

    def __init__(self, params: FDEMForwardParams):
        super().__init__(params)


class FDEMInversionDriver(InversionDriver):
    """Frequency Domain Electromagnetic inversion driver."""

    _params_class = FDEMInversionParams
    _validations = {}
