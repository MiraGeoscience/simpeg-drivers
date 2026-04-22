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
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.ui_json import InputFile
from pydantic import model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.electricals.direct_current.three_dimensions.options import (
    DC3DForwardOptions,
)
from simpeg_drivers.electromagnetics.frequency_domain.options import (
    FDEMForwardOptions,
)
from simpeg_drivers.electromagnetics.time_domain.options import (
    TDEMForwardOptions,
)
from simpeg_drivers.natural_sources.apparent_conductivity.options import (
    AppConForwardOptions,
)
from simpeg_drivers.natural_sources.magnetotellurics.options import (
    MTForwardOptions,
)
from simpeg_drivers.natural_sources.tipper.options import TipperForwardOptions
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from simpeg_drivers.potential_fields.magnetic_vector import (
    MagneticVectorForwardOptions,
)
from simpeg_drivers.utils.synthetics.meshes import MeshOptions

from .models.options import ModelOptions


PARAM_MAP = {
    "apparent conductivty": AppConForwardOptions,
    "gravity": GravityForwardOptions,
    "tdem": TDEMForwardOptions,
    "fem": FDEMForwardOptions,
    "magnetotellurics": MTForwardOptions,
    "direct current 3d": DC3DForwardOptions,
    "magnetic vector": MagneticVectorForwardOptions,
    "tipper": TipperForwardOptions,
}


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
    use_leroi: bool = False
    # _simulation_parameters: BaseForwardOptions | None = None

    @model_validator(mode="before")
    @classmethod
    def use_leroi_em_only(cls, data) -> dict:
        run_command = data["simulation"].options["run_command"]
        is_tem = "time_domain.forward" in run_command
        use_leroi = data.get("use_leroi", False) and is_tem
        data["use_leroi"] = use_leroi
        return data

    # @property
    # def simulation_parameters(self) -> BaseForwardOptions:
    #     """
    #     Create SimPEG parameters from the simulation options.
    #
    #     A new SimPEGGroup is created inside the out_group to store the
    #     result of the forward simulation.
    #     """
    #     if self.simulation_parameters is None:
    #         simulation_options = deepcopy(self.simulation.options)
    #         simulation_options["geoh5"] = self.geoh5
    #         simulation_options["out_group"] = self.simulation
    #
    #         # TODO replace InputFile.data with UIJson.to_params
    #         input_file = InputFile(ui_json=simulation_options, validate=False)
    #         if input_file.ui_json is None:
    #             raise ValueError("Input file must have ui_json set.")
    #
    #         input_file.ui_json["mesh"]["value"] = None
    #
    #         if input_file.data is None:
    #             raise ValueError("Input file data must be set.")
    #
    #         driver = driver_class_from_dict(input_file.data)
    #         return driver._params_class.build(input_file.data)  # pylint: disable=protected-access
