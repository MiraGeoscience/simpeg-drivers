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

from pydantic import model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.joint.params import BaseJointOptions


class JointSurveysOptions(BaseJointOptions):
    """Joint Surveys inversion options."""

    name: ClassVar[str] = "Joint Surveys Inversion"
    title: ClassVar[str] = "Joint Surveys Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_surveys_inversion.ui.json"
    )

    inversion_type: str = "joint surveys"

    @model_validator(mode="after")
    def all_groups_same_physical_property(self):
        physical_properties = [k.options["physical_property"] for k in self.groups]
        if len(list(set(physical_properties))) > 1:
            raise ValueError(
                "All physical properties must be the same. "
                f"Provided SimPEG groups for {physical_properties}."
            )
        return self
