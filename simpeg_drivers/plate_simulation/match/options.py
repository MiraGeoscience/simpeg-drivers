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
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.data import FloatData
from geoh5py.groups import PropertyGroup, SimPEGGroup
from geoh5py.objects import Grid2D, Points
from geoh5py.objects.surveys.electromagnetics.airborne_tem import AirborneTEMReceivers
from pydantic import ConfigDict

from simpeg_drivers import assets_path
from simpeg_drivers.uijson import SimPEGDriversUIJson


class PlateMatchOptions(Options):
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
    title: str = "Plate Match"
    icon: str = "maxwellplate"
    run_command: str = "simpeg_drivers.plate_simulation.match.driver"
    out_group: SimPEGGroup | None = None

    survey: AirborneTEMReceivers
    data: PropertyGroup
    queries: Points
    strike_angles: FloatData | None = None
    max_distance: float = 1000.0
    topography_object: Points | Grid2D
    topography: FloatData | None = None
    simulations: str | Path

    _ui_json_class: ClassVar[type[SimPEGDriversUIJson]] = SimPEGDriversUIJson

    @property
    def simulation_files(self) -> list[Path]:
        """Path to simulation files directory."""
        sim_dir = self.geoh5.h5file.parent / self.simulations
        simulation_files = []

        if not sim_dir.exists():
            raise GeoAppsError("Simulation directory not found. Please revise.")

        for file in sim_dir.iterdir():
            if Path(file).resolve().suffix == ".geoh5":
                simulation_files.append(Path(file))

        return simulation_files
