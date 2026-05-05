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
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.utils import fetch_active_workspace

from simpeg_drivers import assets_path
from simpeg_drivers.options import BaseForwardOptions
from simpeg_drivers.uijson import SimPEGDriversUIJson
from simpeg_drivers.utils.synthetics.meshes import MeshOptions
from simpeg_drivers.utils.utils import driver_class_from_dict

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
    icon: str = "maxwellplate"
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

        ui_json = SimPEGDriversUIJson.from_dict(simulation_options)

        with fetch_active_workspace(self.geoh5) as workspace:
            data = ui_json.to_params(workspace=workspace, validate=False)
            driver = driver_class_from_dict(data)

            return driver._params_class.build(data)  # pylint: disable=protected-access
