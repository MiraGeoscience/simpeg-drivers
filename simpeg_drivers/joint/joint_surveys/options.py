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

from geoh5py.data import FloatData
from pydantic import field_validator, model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.joint.options import BaseJointOptions, JointModelOptions
from simpeg_drivers.options import ModelTypeEnum


class JointSurveysModelOptions(JointModelOptions):
    """
    Joint Surveys model options.

    :param model_type: The physical property type for the inversion.
    :param starting_model: The starting model for the inversion.
    :param reference_model: The reference model for the inversion.
    """

    model_type: ModelTypeEnum = ModelTypeEnum.conductivity
    starting_model: float | FloatData | None = None
    reference_model: float | FloatData | None = None


class JointSurveysOptions(BaseJointOptions):
    """Joint Surveys inversion options."""

    name: ClassVar[str] = "Joint Surveys Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_surveys_inversion.ui.json"
    )

    title: str = "Joint Surveys Inversion"
    inversion_type: str = "joint surveys"

    models: JointSurveysModelOptions

    @field_validator("group_a", "group_b", "group_c")
    @classmethod
    def no_mvi_groups(cls, val):
        if val is None:
            return val

        if "magnetic vector" in val.options.get("inversion_type", ""):
            raise ValueError(
                f"Joint inversion doesn't currently support MVI data as passed in "
                f"the group: {val.name}."
            )
        return val

    @model_validator(mode="after")
    def all_groups_same_physical_property(self):
        physical_properties = [k.options["physical_property"] for k in self.groups]
        if len(list(set(physical_properties))) > 1:
            raise ValueError(
                "All physical properties must be the same. "
                f"Provided SimPEG groups for {physical_properties}."
            )

        self.physical_property = physical_properties[0]
        return self
