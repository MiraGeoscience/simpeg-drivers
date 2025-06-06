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

from geoh5py.data import ReferencedData
from geoh5py.objects import Octree

from simpeg_drivers import assets_path
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.options import ModelOptions


class JointPetrophysicsModelOptions(ModelOptions):
    """
    Model options with petrophysics reference model.

    :param petrophysics: The reference geology data.
    """

    petrophysics_model: ReferencedData


class JointPetrophysicsOptions(BaseJointOptions):
    """
    Joint Petrophysically Guided Inversion (PGI) driver.

    :param mesh: The global mesh entity containing the reference geology.
    :param petrophysics_model: The reference geology data.
    """

    name: ClassVar[str] = "Petrophysically Guided Inversion (PGI)"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_petrophysics_inversion.ui.json"
    )

    title: str = "Joint Petrophysically Guided Inversion (PGI)"
    physical_property: list[str] = [""]

    inversion_type: str = "joint petrophysics"

    group_b_multiplier: float | None = None
    mesh: Octree
    petrophysics_model: JointPetrophysicsModelOptions
