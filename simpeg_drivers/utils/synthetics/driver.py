# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.data import BooleanData, FloatData
from geoh5py.objects import DrapeModel, ObjectBase, Octree, Surface

from simpeg_drivers.utils.synthetics.meshes import get_mesh
from simpeg_drivers.utils.synthetics.models import get_model
from simpeg_drivers.utils.synthetics.options import SyntheticsComponentsOptions
from simpeg_drivers.utils.synthetics.surveys.factory import get_survey
from simpeg_drivers.utils.synthetics.topography import (
    get_active,
    get_topography_surface,
)


class SyntheticsComponents:
    """Creates a workspace populated with objects for simulation and subsequent inversion."""

    def __init__(
        self,
        geoh5: Workspace,
        options: SyntheticsComponentsOptions | None = None,
    ):
        if options is None:
            options = SyntheticsComponentsOptions()

        self.geoh5 = geoh5
        self.options = options
        self._topography: Surface | None = None
        self._survey: ObjectBase | None = None
        self._mesh: Octree | DrapeModel | None = None
        self._active: FloatData | None = None
        self._model: FloatData | None = None

    @property
    def topography(self) -> Surface:
        if self._topography is None:
            entity = self.geoh5.get_entity("topography")[0]

            if entity is None:
                entity = get_topography_surface(
                    geoh5=self.geoh5,
                    options=self.options,
                )
            self._topography = entity
        return self._topography

    @property
    def survey(self) -> ObjectBase:
        if self._survey is None:
            entity = self.geoh5.get_entity(self.options.survey.name)[0]

            if entity is None:
                entity = get_survey(
                    geoh5=self.geoh5,
                    method=self.options.method,
                    options=self.options.survey,
                )
            self._survey = entity
        return self._survey

    @property
    def mesh(self) -> Octree | DrapeModel:
        if self._mesh is None:
            entity = self.geoh5.get_entity("mesh")[0]

            if entity is None:
                entity = get_mesh(
                    self.options.method,
                    survey=self.survey,
                    topography=self.topography,
                    options=self.options.mesh,
                    plate=self.options.model.plate
                    if self.options.refine_plate
                    else None,
                )
            self._mesh = entity

        return self._mesh

    @property
    def active(self) -> FloatData:
        if self._active is None:
            entity = self.mesh.get_entity(self.options.active.name)[0]

            if entity is None:
                entity = get_active(self.mesh, self.topography)
            self._active = entity

        return self._active

    @property
    def model(self) -> FloatData:
        if self._model is None:
            entity = self.mesh.get_entity(self.options.model.name)[0]
            if entity is None:
                entity = get_model(
                    method=self.options.method,
                    mesh=self.mesh,
                    active=self.active.values,
                    options=self.options.model,
                )
            self._model = entity
        return self._model
