# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
#  All rights reserved.
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


class SensitivityCutoffParams(BaseData):
    """
    Contour parameters for use with `contours.driver`.

    :param contours: Contouring parameters.
    :param source: Parameters for the source object and data.
    :param output: Output
    """

    name: ClassVar[str] = "sensitivity_cutoff"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/sensitivity_cutoff.ui.json"
    )
    title: ClassVar[str] = "Sensitivity Cutoff Depth of Investigation"
    run_command: ClassVar[str] = (
        "simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver"
    )

    conda_environment: str = "simpeg_drivers"
    mesh: Octree
    sensitivity_model: FloatData
    sensitivity_cutoff: float = 0.1
    mask_name: str | None = "Sensitivity Cutoff"

    @field_validator("mask_name")
    @classmethod
    def default_mask_name(cls, value):
        if value is None:
            value = "Sensitivity Cutoff"
        return value
