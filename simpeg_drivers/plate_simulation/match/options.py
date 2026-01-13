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
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.objects import Grid2D, Points
from geoh5py.objects.surveys.electromagnetics.airborne_tem import AirborneTEMReceivers
from pydantic import ConfigDict

from simpeg_drivers import assets_path


class MatchOptions(Options):
    """
    Options for matching signal from a survey against a library of simulations.

    :param survey: A Time-Domain Airborne TEM survey object.
    :param data: A property group containing observed data.
    :param queries: A Points object containing the target locations.
    :param strike_angles: An optional data array containing strike angles for each
        target location.
    :param simulations: Directory to store simulation files.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    name: ClassVar[str] = "plate_match"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/plate_match.ui.json"
    title: ClassVar[str] = "Plate Match"
    run_command: ClassVar[str] = "simpeg_drivers.plate_simulation.match.driver"
    out_group: SimPEGGroup | None = None

    survey: AirborneTEMReceivers
    data: PropertyGroup
    queries: Points
    strike_angles: np.ndarray | None = None
    max_distance: float = 1000.0
    topography_object: Points | Grid2D
    topography: np.ndarray | None = None
    simulations: ClassVar[Path]
