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

from geoh5py.data import FloatData
from geoh5py.groups import PropertyGroup, SimPEGGroup
from pydantic import ConfigDict

from simpeg_drivers.options import (
    CoolingSceduleOptions,
    CoreOptions,
    DirectiveOptions,
    IRLSOptions,
    ModelOptions,
    OptimizationOptions,
)


class JointModelOptions(ModelOptions):
    """
    Model options with petrophysics reference model.

    :param petrophysical: The reference geology data.
    """

    starting_model: None = None
    reference_model: None = None
    lower_bound: float | FloatData | None = None
    upper_bound: float | FloatData | None = None

    # Model values for regularization
    alpha_s: float | FloatData | None | None = None
    length_scale_x: float | FloatData | None = None
    length_scale_y: float | FloatData | None = None
    length_scale_z: float | FloatData | None = None
    gradient_rotation: PropertyGroup | None = None

    # Model values for IRLS
    s_norm: float | FloatData | None = None
    x_norm: float | FloatData | None = None
    y_norm: float | FloatData | None = None
    z_norm: float | FloatData | None = None


class BaseJointOptions(CoreOptions):
    """
    Base Joint Options.

    :param group_a: First SimPEGGroup with options set for inversion.
    :param group_a_multiplier: Multiplier for the data misfit function for Group A.
    :param group_b: Second SimPEGGroup with options set for inversion.
    :param group_b_multiplier: Multiplier for the data misfit function for Group B.
    :param group_c: Third SimPEGGroup with options set for inversion.
    :param group_c_multiplier: Multiplier for the data misfit function for Group C.
    """

    model_config = ConfigDict(frozen=False)

    forward_only: bool = False
    physical_property: str | None = ""

    group_a: SimPEGGroup
    group_a_multiplier: float = 1.0
    group_b: SimPEGGroup
    group_b_multiplier: float = 1.0
    group_c: SimPEGGroup | None = None
    group_c_multiplier: float | None = None

    irls: IRLSOptions = IRLSOptions()
    directives: DirectiveOptions = DirectiveOptions(auto_scale_misfits=True)
    cooling_schedule: CoolingSceduleOptions = CoolingSceduleOptions()
    optimization: OptimizationOptions = OptimizationOptions()

    store_sensitivities: str = "ram"

    @property
    def groups(self) -> list[SimPEGGroup]:
        """List all active groups."""
        return [k for k in [self.group_a, self.group_b, self.group_c] if k is not None]
