# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
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

from pathlib import Path
from typing import ClassVar

from geoapps_utils.driver.data import BaseData
from geoh5py.data import FloatData
from geoh5py.objects import Octree
from pydantic import field_validator

from simpeg_drivers import assets_path


class SensitivityCutoffOptions(BaseData):
    """
    Sensitivity cutoff parameters for depth of investigation studies.

    :param mesh: Octree mesh containing saved sensitivities.
    :param sensitivity_model: Saved row-sum-squared sensitivity data.
    :param sensitivity_cutoff: Sensitivity percentage below which the
        model's influence to the data is considered negligible.
    :param mask_name: Base name given to the mask and scaled
        sensitivities.
    """

    name: ClassVar[str] = "sensitivity_cutoff"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/sensitivity_cutoff.ui.json"
    )

    title: str = "Depth of Investigation: Sensitivity Cutoff"
    run_command: str = "simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver"

    conda_environment: str = "simpeg_drivers"
    mesh: Octree
    sensitivity_model: FloatData
    sensitivity_cutoff: float = 0.1
    cutoff_method: str = "percentile"
    mask_name: str | None = "Sensitivity Cutoff"

    @field_validator("mask_name")
    @classmethod
    def default_mask_name(cls, value):
        if value is None:
            value = "Sensitivity Cutoff"
        return value
