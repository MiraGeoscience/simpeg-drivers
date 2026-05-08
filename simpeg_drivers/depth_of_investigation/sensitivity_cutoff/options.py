# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path
from typing import ClassVar

from geoapps_utils.base import Options
from geoh5py.data import FloatData
from geoh5py.objects import DrapeModel, Octree
from pydantic import field_validator

from simpeg_drivers import assets_path


class SensitivityCutoffOptions(Options):
    """
    Sensitivity cutoff parameters for depth of investigation studies.

    :param mesh: Octree mesh or DrapeModel containing saved sensitivities.
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
    icon: str = "grd"
    run_command: str = "simpeg_drivers.depth_of_investigation.sensitivity_cutoff.driver"

    conda_environment: str = "simpeg_drivers"
    mesh: Octree | DrapeModel
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
