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

import numpy as np
from geoh5py.objects.surveys.electromagnetics.ground_tem import (
    LargeLoopGroundTEMReceivers,
)

from simpeg_drivers.driver import InversionDriver

from .options import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)


class TDEMForwardDriver(InversionDriver):
    """Time Domain Electromagnetic forward driver."""

    _params_class = TDEMForwardOptions


class TDEMInversionDriver(InversionDriver):
    """Time Domain Electromagnetic inversion driver."""

    _params_class = TDEMInversionOptions
