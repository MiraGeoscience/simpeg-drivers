# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from typing import TypeVar

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.objects import Points
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


T = TypeVar("T")


class PlateOptions(BaseModel):
    """
    Parameters describing an anomalous plate.

    :param name: Name given to the plate.
    :param plate_property: Value given to the plate(s).
    :param geometry: Parameters describing the plate geometry.
    :param number: Number of offset plates to be created.
    :param spacing: Spacing between plates.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "Plate"
    plate_property: float = Field(
        validation_alias=AliasChoices("plate_property", "plate")
    )
    geometry: PlateModel
    number: int = 1
    spacing: float = 0.0

    @model_validator(mode="after")
    def single_plate(self):
        if self.number == 1:
            self.spacing = 0.0
        return self

    def center(
        self,
        survey: Points,
        surface: Points,
    ) -> tuple[float, float, float]:
        """
        Find the plate center relative to a survey and topography.

        :param survey: geoh5py survey object for plate simulation.
        :param surface: Points-like object to reference plate depth from.
        :param depth_offset: Additional offset to be added to the depth of the plate.
        """

        xy = (
            survey.vertices[:, 0].mean() + self.geometry.origin[0],
            survey.vertices[:, 1].mean() + self.geometry.origin[1],
        )
        z_topo = topography_above_point(topography=surface, point=xy)  # TODO

        return xy + (z_topo - self.geometry.elevation,)


class OverburdenOptions(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param overburden_property: Value given to the overburden layer.
    """

    thickness: float
    overburden_property: float = Field(
        validation_alias=AliasChoices("overburden_property", "overburden")
    )


class ModelOptions(BaseModel):
    """
    Parameters for the blackground + overburden and plate model.

    :param background: Value given to the background.
    :param overburden: Overburden layer parameters.
    :param plate: Plate parameters.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    background: float
    overburden_options: OverburdenOptions
    plate_options: PlateOptions
