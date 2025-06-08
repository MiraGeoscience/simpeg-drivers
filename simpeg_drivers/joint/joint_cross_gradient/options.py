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
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.options import ModelOptions


class JointCrossGradientModelOptions(ModelOptions):
    """
    Model options with petrophysics reference model.

    :param petrophysical: The reference geology data.
    """

    starting_model: None = None


class JointCrossGradientOptions(BaseJointOptions):
    """
    Joint Cross Gradient inversion options.

    :param cross_gradient_weight_a_b:  Weight applied to the cross gradient
        regularization between the first and second models.
    :param cross_gradient_weight_c_a:  Weight applied to the cross gradient
        regularization between the first and third models.
    :param cross_gradient_weight_c_b:  Weight applied to the cross gradient
        regularization between the second and third model.
    """

    name: ClassVar[str] = "Joint Cross Gradient Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_cross_gradient_inversion.ui.json"
    )

    title: str = "Joint Cross Gradient Inversion"
    inversion_type: str = "joint cross gradient"

    mesh: Octree | None = None
    cross_gradient_weight_a_b: float = 1.0
    cross_gradient_weight_c_a: float | None = None
    cross_gradient_weight_c_b: float | None = None

    models: JointCrossGradientModelOptions = JointCrossGradientModelOptions()
