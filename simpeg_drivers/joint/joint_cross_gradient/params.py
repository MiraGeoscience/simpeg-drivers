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

from pathlib import Path
from typing import ClassVar

from geoh5py.objects import Octree

from simpeg_drivers import assets_path
from simpeg_drivers.joint.params import BaseJointOptions


class JointCrossGradientOptions(BaseJointOptions):
    """
    Joint Cross Gradient inversion options.

    :param cross_gradient_weight_a_b:  Weight applied to the cross gradient
        regularizations.
    :param cross_gradient_weight_c_a:  Weight applied to the cross gradient
        regularizations.
    :param cross_gradient_weight_c_b:  Weight applied to the cross gradient
        regularizations.
    """

    name: ClassVar[str] = "Joint Cross Gradient Inversion"
    title: ClassVar[str] = "Joint Cross Gradient Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_cross_gradient_inversion.ui.json"
    )

    inversion_type: str = "joint cross gradient"

    data_object: None = None
    mesh: Octree | None = None
    starting_model: None = None
    cross_gradient_weight_a_b: float = 1.0
    cross_gradient_weight_c_a: float | None = None
    cross_gradient_weight_c_b: float | None = None
