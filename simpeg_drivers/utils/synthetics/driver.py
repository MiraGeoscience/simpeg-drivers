# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoh5py import Workspace
from geoh5py.data import FloatData
from geoh5py.objects import DrapeModel, ObjectBase, Octree, Surface

from simpeg_drivers.utils.synthetics.meshes.factory import get_mesh
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
    def topography(self):
        entity = self.geoh5.get_entity("topography")[0]
        assert isinstance(entity, Surface | type(None))
        if entity is None:
            assert self.options is not None
            entity = get_topography_surface(
                geoh5=self.geoh5,
                options=self.options.survey,
            )
        self._topography = entity
        return self._topography

    @property
    def survey(self):
        entity = self.geoh5.get_entity(self.options.survey.name)[0]
        assert isinstance(entity, ObjectBase | type(None))
        if entity is None:
            assert self.options is not None
            entity = get_survey(
                geoh5=self.geoh5,
                method=self.options.method,
                options=self.options.survey,
            )
        self._survey = entity
        return self._survey

    @property
    def mesh(self):
        entity = self.geoh5.get_entity(self.options.mesh.name)[0]
        assert isinstance(entity, Octree | DrapeModel | type(None))
        if entity is None:
            assert self.options is not None
            entity = get_mesh(
                self.options.method,
                survey=self.survey,
                topography=self.topography,
                options=self.options.mesh,
            )
        self._mesh = entity
        return self._mesh

    @property
    def active(self):
        entity = self.geoh5.get_entity(self.options.active.name)[0]
        assert isinstance(entity, FloatData | type(None))
        if entity is None:
            entity = get_active(self.mesh, self.topography)
        self._active = entity
        return self._active

    @property
    def model(self):
        entity = self.geoh5.get_entity(self.options.model.name)[0]
        assert isinstance(entity, FloatData | type(None))
        if entity is None:
            assert self.options is not None
            entity = get_model(
                method=self.options.method,
                mesh=self.mesh,
                active=self.active.values,
                options=self.options.model,
            )
        self._model = entity
        return self._model
