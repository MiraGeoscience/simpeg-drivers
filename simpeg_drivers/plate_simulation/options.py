# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from copy import deepcopy
from pathlib import Path
from typing import ClassVar

from geoapps_utils.base import Options
from geoapps_utils.run import fetch_driver_class_from_string
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.ui_json import InputFile

from simpeg_drivers import assets_path
from simpeg_drivers.driver import from_input_file
from simpeg_drivers.options import BaseForwardOptions
from simpeg_drivers.utils.synthetics.meshes import MeshOptions

from .models.options import ModelOptions


class PlateSimulationOptions(Options):
    """
    Parameters for the plate simulation driver.

    geoh5: Workspace in which the model will be built and results stored.
    mesh: Parameters for the octree mesh.
    model: Parameters for the background + overburden and plate model.
    simulation: Simpeg group containing simulation options and a survey.  Any
        mesh or starting model selections will be replaced by the objects
        created by the driver.
    """

    name: ClassVar[str] = "plate_simulation"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/plate_simulation.ui.json"
    title: str = "Plate Simulation"
    run_command: str = "simpeg_drivers.plate_simulation.driver"
    out_group: SimPEGGroup | UIJsonGroup | None = None
    forward_only: bool = True
    inversion_type: str = "plate simulation"

    mesh: MeshOptions
    model: ModelOptions
    simulation: SimPEGGroup | UIJsonGroup

    def simulation_parameters(self) -> BaseForwardOptions:
        """
        Create SimPEG parameters from the simulation options.

        A new SimPEGGroup is created inside the out_group to store the
        result of the forward simulation.
        """
        simulation_options = deepcopy(self.simulation.options)
        simulation_options["geoh5"] = self.geoh5

        input_file = InputFile(ui_json=simulation_options, validate=False)
        if input_file.ui_json is None:
            raise ValueError("Input file must have ui_json set.")

        input_file.ui_json["mesh"]["value"] = None

        if input_file.data is None:
            raise ValueError("Input file data must be set.")

        driver = None
        if input_file.data.get("inversion_type", None):
            driver = from_input_file(input_file.data)

        if input_file.data.get("run_command", None):
            driver = fetch_driver_class_from_string(input_file.data["run_command"])

        if driver:
            return driver._params_class.build(input_file.data)  # pylint: disable=protected-access

        raise NotImplementedError(
            f"Unknown inversion type: {input_file.data['inversion_type']}"
        )
