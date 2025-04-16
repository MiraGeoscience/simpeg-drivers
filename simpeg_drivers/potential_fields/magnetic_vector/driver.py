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

from simpeg import maps

from simpeg_drivers.driver import InversionDriver

from .options import MVIForwardOptions, MVIInversionOptions


class MVIForwardDriver(InversionDriver):
    """Magnetic Vector forward driver."""

    _options_class = MVIForwardOptions
    _validations = None


class MVIInversionDriver(InversionDriver):
    """Magnetic Vector inversion driver."""

    _options_class = MVIInversionOptions
    _validations = None

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
