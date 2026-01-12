# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import itertools
from pathlib import Path
from typing import ClassVar

import numpy as np
from geoapps_utils.base import Options
from geoh5py.groups import PropertyGroup, UIJsonGroup
from geoh5py.objects import Points
from geoh5py.objects.surveys.electromagnetics.airborne_tem import AirborneTEMReceivers
from geoh5py.shared.utils import stringify
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, field_serializer

from simpeg_drivers import assets_path


class MatchOptions(Options):
    """
    Options for matching signal from a survey against a library of simulations.

    :param survey: A Time-Domain Airborne TEM survey object.
    :param data: A property group containing observed data.
    :param targets: A Points object containing the target locations.
    :param strike_angles: An optional data array containing strike angles for each
        target location.
    :param simulations: Directory to store simulation files.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    name: ClassVar[str] = "plate_match"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/plate_match.ui.json"
    title: ClassVar[str] = "Plate Match"
    run_command: ClassVar[str] = "simpeg_drivers.plate_simulation.match.driver"
    out_group: UIJsonGroup | None = None

    survey: AirborneTEMReceivers
    data: PropertyGroup
    targets: Points
    strike_angles: np.ndarray | None = None
    simulations: ClassVar[Path]
