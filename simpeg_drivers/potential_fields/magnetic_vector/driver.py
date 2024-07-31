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

from simpeg import maps

from simpeg_drivers.driver import InversionDriver

from .constants import validations
from .params import MagneticVectorParams


class MagneticVectorDriver(InversionDriver):
    _params_class = MagneticVectorParams
    _validations = validations

    def __init__(self, params: MagneticVectorParams):
        super().__init__(params)

    @property
    def mapping(self) -> list[maps.Projection] | None:
        """Model mapping for the inversion."""
        if self._mapping is None:
            mapping = []
            start = 0
            for _ in range(3):
                mapping.append(
                    maps.Projection(
                        self.n_values * 3, slice(start, start + self.n_values)
                    )
                )
                start += self.n_values

            self._mapping = mapping

        return self._mapping

    @mapping.setter
    def mapping(self, value: list[maps.Projection]):
        if not isinstance(value, list) or len(value) != 3:
            raise TypeError(
                "'mapping' must be a list of 3 instances of maps.IdentityMap. "
                f"Provided {value}"
            )

        if not all(
            isinstance(val, maps.Projection)
            and val.shape == (self.n_values, 3 * self.n_values)
            for val in value
        ):
            raise TypeError(
                "'mapping' must be an instance of maps.Projection with shape (n_values, 3 * self.n_values). "
                f"Provided {value}"
            )

        self._mapping = value
