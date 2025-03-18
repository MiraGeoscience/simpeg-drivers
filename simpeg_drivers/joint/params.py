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

from geoh5py.groups import SimPEGGroup

from simpeg_drivers.params import BaseInversionOptions


class BaseJointOptions(BaseInversionOptions):
    """
    Base Joint Options.

    :param group_a: First SimPEGGroup with options set for inversion.
    :param group_a_multiplier: Multiplier for the data misfit function for Group A.
    :param group_b: Second SimPEGGroup with options set for inversion.
    :param group_b_multiplier: Multiplier for the data misfit function for Group B.
    :param group_c: Third SimPEGGroup with options set for inversion.
    :param group_c_multiplier: Multiplier for the data misfit function for Group C.
    """

    group_a: SimPEGGroup
    group_a_multiplier: float = 1.0
    group_b: SimPEGGroup
    group_b_multiplier: float = 1.0
    group_c: SimPEGGroup | None = None
    group_c_multiplier: float | None = None

    @property
    def groups(self) -> list[SimPEGGroup]:
        """List all active groups."""
        return [k for k in [self.group_a, self.group_b, self.group_c] if k is not None]
