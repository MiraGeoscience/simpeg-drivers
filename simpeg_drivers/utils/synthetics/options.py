# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from collections.abc import Callable

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.locations import gaussian
from geoh5py.objects import ObjectBase, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace
from grid_apps.octree_creation.options import OctreeOptions
from pydantic import BaseModel, ConfigDict

from simpeg_drivers.options import DrapeModelOptions


class SurveyOptions(BaseModel):
    """Parameters for configuring a synthetic survey grid."""

    center: tuple[float, float] = (0.0, 0.0)
    width: float = 200.0
    height: float = 200.0
    drape: float = 0.0
    n_stations: int = 20
    n_lines: int = 5
    rotation: float = 0.0
    topography: Callable = lambda x, y: gaussian(x, y, amplitude=50.0, width=100.0)
    name: str = "survey"

    @property
    def limits(self) -> list[float]:
        """East-West bounding box of the survey as [xmin, xmax, ymin, ymax]."""
        return [
            self.center[0] - self.width / 2,
            self.center[0] + self.width / 2,
            self.center[1] - self.height / 2,
            self.center[1] + self.height / 2,
        ]


class MeshOptions(BaseModel):
    """Core parameters for octree mesh creation."""

    u_cell_size: float = 5.0
    v_cell_size: float = 5.0
    w_cell_size: float = 5.0
    padding_distance: float = 100.0
    depth_core: float = 100.0
    max_distance: float = 100.0
    minimum_level: int = 8
    diagonal_balance: bool = True
    survey_refinement: list[int] = [4, 6]
    topography_refinement: list[int] = [0, 0, 1]
    plate_refinement: list[int] = [4]
    name: str = "mesh"

    @property
    def cell_size(self) -> tuple[float, float, float]:
        """Cell size in the u, v, and w directions."""
        return (self.u_cell_size, self.v_cell_size, self.w_cell_size)

    def octree_params(
        self, survey: ObjectBase, topography: Surface, plates: list[Surface] | None
    ) -> OctreeOptions:
        """
        Collect parameters for an OctreeDriver run for a synthetic experiment.

        :param survey: Survey object used as the primary refinement source.
        :param topography: Surface used for topographic mesh refinement.
        :param plates: Optional list of plate surfaces for additional refinement.

        :return: OctreeOptions instance ready to be passed to an OctreeDriver.
        """

        locs = survey.vertices.copy()
        locs = np.vstack([locs, locs - np.r_[self.cell_size] / 2])
        with fetch_active_workspace(survey.workspace) as geoh5:
            survey = Points.create(geoh5, vertices=locs)

        refinements = [
            {
                "refinement_object": survey,
                "levels": self.survey_refinement,
                "horizon": False,
            },
            {
                "refinement_object": survey,
                "levels": self.survey_refinement,
                "horizon": False,
            },
            {
                "refinement_object": topography,
                "levels": self.topography_refinement,
                "horizon": False,
                "distance": 1000.0,
            },
        ]

        if plates is not None:
            for plate in plates:
                refinements.append(
                    {
                        "refinement_object": plate,
                        "levels": self.plate_refinement,
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


class ModelOptions(BaseModel):
    """Parameters controlling physical properties and plate geometry."""

    background: float = 0.0
    anomaly: float = 1.0
    plate: PlateModel = PlateModel(
        strike_length=40.0,
        dip_length=40.0,
        width=40.0,
        easting=0.0,
        northing=0.0,
        elevation=30.0,
        dip=90.0,
        direction=0.0,
    )
    name: str = "model"


class ActiveCellsOptions(BaseModel):
    """Options for naming the active cells model."""

    name: str = "active_cells"


class SyntheticsComponentsOptions(BaseModel):
    """Top-level options for configuring a synthetic inversion experiment."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    method: str = "gravity"
    refine_plate: bool = False
    survey: SurveyOptions = SurveyOptions()
    mesh: MeshOptions | DrapeModelOptions = MeshOptions()
    model: ModelOptions = ModelOptions()
    active: ActiveCellsOptions = ActiveCellsOptions()
