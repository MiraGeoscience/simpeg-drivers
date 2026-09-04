# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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

from geoapps_utils.run import fetch_driver_class_from_string
from geoh5py.data import FloatData, IntegerData
from pydantic import model_validator

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

    model_type: ModelTypeEnum | None = None
    starting_model: float | FloatData | IntegerData | None = None
    reference_model: float | FloatData | IntegerData | None = None


class JointSurveysOptions(BaseJointOptions):
    """Joint Surveys inversion options."""

    name: ClassVar[str] = "Joint Surveys Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/joint_surveys_inversion.ui.json"
    )
    run_command: str = "simpeg_drivers.joint.joint_surveys.driver"
    title: str = "Joint Surveys Inversion"
    icon: str = "model"
    inversion_type: str = "joint surveys"

    models: JointSurveysModelOptions

    @model_validator(mode="after")
    def all_groups_same_physical_property(self):
        physical_properties = []
        for group in self.groups:
            driver_class = fetch_driver_class_from_string(group.options["run_command"])
            physical_properties.append(
                driver_class._params_class.model_construct().physical_property  # pylint: disable=protected-access
            )

        if len(list(set(physical_properties))) > 1:
            raise ValueError(
                "All physical properties must be the same. "
                f"Provided SimPEG groups for {physical_properties}."
            )

        self.physical_property = physical_properties[0]
        return self
