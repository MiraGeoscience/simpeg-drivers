# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from collections.abc import Callable

from geoapps_utils.modelling.plates import PlateModel
from geoapps_utils.utils.locations import gaussian
from pydantic import BaseModel, ConfigDict


class SurveyOptions(BaseModel):
    center: tuple[float, float] = (0.0, 0.0)
    width: float = 200.0
    height: float = 200.0
    drape: float = 0.0
    n_stations: int = 20
    n_lines: int = 5
    topography: Callable = lambda x, y: gaussian(x, y, amplitude=50.0, width=100.0)
    name: str = "survey"

    @property
    def limits(self) -> list[float]:
        return [
            self.center[0] - self.width / 2,
            self.center[0] + self.width / 2,
            self.center[1] - self.height / 2,
            self.center[1] + self.height / 2,
        ]


class MeshOptions(BaseModel):
    cell_size: tuple[float, float, float] = (5.0, 5.0, 5.0)
    refinement: tuple = (4, 6)
    padding_distance: float = 100.0
    name: str = "mesh"


class ModelOptions(BaseModel):
    background: float = 0.0
    anomaly: float = 1.0
    plate: PlateModel = PlateModel(
        strike_length=40.0,
        dip_length=40.0,
        width=40.0,
        origin=(0.0, 0.0, 10.0),
    )
    name: str = "model"


class ActiveCellsOptions(BaseModel):
    name: str = "active_cells"


class SyntheticsComponentsOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    method: str = "gravity"
    survey: SurveyOptions = SurveyOptions()
    mesh: MeshOptions = MeshOptions()
    model: ModelOptions = ModelOptions()
    active: ActiveCellsOptions = ActiveCellsOptions()
