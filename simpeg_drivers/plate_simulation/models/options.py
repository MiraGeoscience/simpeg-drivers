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
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)


T = TypeVar("T")


class PlateOptions(BaseModel):
    """
    Parameters describing an anomalous plate.

    :param plate: Value given to the plate(s).
    :param geometry: Parameters describing the plate geometry.
    :param reference: Point of rotation to be 'center' or 'top'.
    :param number: Number of offset plates to be created.
    :param spacing: Spacing between plates.
    :param relative_locations: If True locations are relative to survey in xy and
        mean topography in z.
    :param reference_surface: Switches between using topography and overburden as
        elevation reference of the plate.
    :param reference_type: Type of reference for plate elevation.  Can be 'mean'
        'min', or 'max'.  Resulting elevation will be relative to the mean,
        minimum, or maximum of the reference surface.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "Plate"
    plate_property: float
    geometry: PlateModel
    number: int = 1
    spacing: float = 0.0
    relative_locations: bool = False
    reference_surface: str = "topography"
    reference_type: str = "mean"

    @field_validator("reference_surface", "reference_type", mode="before")
    @classmethod
    def none_to_default(cls, value: T | None, info: ValidationInfo) -> T:
        return value or cls.model_fields[info.field_name].default  # pylint: disable=unsubscriptable-object

    @model_validator(mode="after")
    def single_plate(self):
        if self.number == 1:
            self.spacing = 0.0
        return self

    @property
    def halfplate(self):
        """Compute half the z-projection length of the plate."""
        return 0.5 * self.geometry.dip_length * np.sin(np.deg2rad(self.geometry.dip))

    def center(
        self,
        survey: Points,
        surface: Points,
        depth_offset: float = 0.0,
    ) -> tuple[float, float, float]:
        """
        Find the plate center relative to a survey and topography.

        :param survey: geoh5py survey object for plate simulation.
        :param surface: Points-like object to reference plate depth from.
        :param depth_offset: Additional offset to be added to the depth of the plate.
        """
        return *self._get_xy(survey), self._get_z(surface, depth_offset)

    def _get_xy(self, survey: Points) -> tuple[float, float]:
        """Return true or relative locations in x and y."""

        if self.relative_locations:
            return (
                survey.vertices[:, 0].mean() + self.geometry.origin[0],
                survey.vertices[:, 1].mean() + self.geometry.origin[1],
            )

        return self.geometry.origin[0], self.geometry.origin[1]

    def _get_z(self, surface: Points, offset: float = 0.0) -> float:
        """
        Return true or relative locations in z.

        :param surface: Points-like object to reference plate depth from.
        :offset: Additional offset to be added to the depth.

        """
        if surface.vertices is None:
            raise ValueError("Topography object has no vertices.")
        if self.relative_locations:
            z = getattr(surface.vertices[:, 2], self.reference_type)()
            z += offset + self.geometry.elevation - self.halfplate
        else:
            z = self.geometry.elevation

        return z


class OverburdenOptions(BaseModel):
    """
    Parameters for the overburden layer.

    :param thickness: Thickness of the overburden layer.
    :param overburden: Value given to the overburden layer.
    """

    thickness: float
    overburden_property: float


class ModelOptions(BaseModel):
    """
    Parameters for the blackground + overburden and plate model.

    :param background: Value given to the background.
    :param overburden: Overburden layer parameters.
    :param plate: Plate parameters.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    background: float
    overburden: OverburdenOptions
    plate: PlateOptions
