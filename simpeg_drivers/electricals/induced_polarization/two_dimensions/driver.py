#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from simpeg_drivers.driver import InversionDriver

from .constants import validations
from .params import InducedPolarization2DParams


class InducedPolarization2DDriver(InversionDriver):
    _params_class = InducedPolarization2DParams
    _validations = validations

    def __init__(self, params: InducedPolarization2DParams):
        super().__init__(params)
