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
    IP3DForwardParams,
    IP3DInversionParams,
)


class IP3DForwardDriver(InversionDriver):
    """Induced Polarization 3D forward driver."""

    _params_class = IP3DForwardParams
    _validations = {}


class IP3DInversionDriver(InversionDriver):
    """Induced Polarization 3D inversion driver."""

    _params_class = IP3DInversionParams
    _validations = {}
