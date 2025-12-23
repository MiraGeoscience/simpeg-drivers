# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
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
from geoh5py.objects import ObjectBase, Points, Surface
from geoh5py.ui_json import InputFile
from grid_apps.octree_creation.options import OctreeOptions
from pydantic import BaseModel

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
from simpeg_drivers.natural_sources.magnetotellurics.options import (
    MTForwardOptions,
)
from simpeg_drivers.natural_sources.tipper.options import TipperForwardOptions
from simpeg_drivers.options import BaseForwardOptions
from simpeg_drivers.potential_fields.gravity.options import GravityForwardOptions
from simpeg_drivers.potential_fields.magnetic_vector.options import (
    MVIForwardOptions,
)

from .models.options import ModelOptions


PARAM_MAP = {
    "gravity": GravityForwardOptions,
    "tdem": TDEMForwardOptions,
    "fem": FDEMForwardOptions,
    "magnetotellurics": MTForwardOptions,
    "direct current 3d": DC3DForwardOptions,
    "magnetic vector": MVIForwardOptions,
    "tipper": TipperForwardOptions,
}


class MeshOptions(BaseModel):
    """Core parameters for octree mesh creation."""

    u_cell_size: float
    v_cell_size: float
    w_cell_size: float
    padding_distance: float
    depth_core: float
    max_distance: float
    minimum_level: int = 8
    diagonal_balance: bool = False

    def octree_params(
        self, survey: ObjectBase, topography: Surface | Points, plates: list[Surface]
    ):
        refinements = [
            {
                "refinement_object": survey,
                "levels": [4, 4, 4],
                "horizon": False,
            },
            {
                "refinement_object": topography,
                "levels": [0, 2],
                "horizon": True,
                "distance": 1000.0,
            },
        ]
        for plate in plates:
            refinements.append(
                {
                    "refinement_object": plate,
                    "levels": [2, 1],
                    "horizon": False,
                }
            )

        octree_params = OctreeOptions(
            geoh5=survey.workspace,
            objects=survey,
            u_cell_size=self.u_cell_size,
            v_cell_size=self.v_cell_size,
            w_cell_size=self.w_cell_size,
            horizontal_padding=self.padding_distance,
            vertical_padding=self.padding_distance,
            depth_core=self.depth_core,
            max_distance=self.max_distance,
            minimum_level=self.minimum_level,
            diagonal_balance=self.diagonal_balance,
            refinements=refinements,
        )
        return octree_params


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
    title: ClassVar[str] = "Plate Simulation"
    run_command: ClassVar[str] = "simpeg_drivers.plate_simulation.driver"
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
        simulation_options["forward_only"] = (
            True  # TODO remove this when mechanics use ForwardOptions
        )

        input_file = InputFile(ui_json=simulation_options, validate=False)
        if input_file.ui_json is None:
            raise ValueError("Input file must have ui_json set.")

        input_file.ui_json["mesh"]["value"] = None

        if input_file.data is None:
            raise ValueError("Input file data must be set.")

        if input_file.data["inversion_type"] in PARAM_MAP:
            return PARAM_MAP[input_file.data["inversion_type"]].build(input_file.data)

        raise NotImplementedError(
            f"Unknown inversion type: {input_file.data['inversion_type']}"
        )
