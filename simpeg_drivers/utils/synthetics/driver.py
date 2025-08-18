# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from geoh5py import Workspace

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
        self, geoh5: Workspace, options: SyntheticsComponentsOptions | None = None
    ):
        self.geoh5 = geoh5
        self.options = options
        self._topography = None
        self._survey = None
        self._mesh = None
        self._active = None
        self._model = None

    @property
    def topography(self):
        self._topography = self.geoh5.get_entity("topography")[0]
        if self._topography is None:
            assert self.options is not None
            self._topography = get_topography_surface(
                geoh5=self.geoh5,
                options=self.options.survey,
            )
        return self._topography

    @property
    def survey(self):
        self._survey = self.geoh5.get_entity(self.options.survey.name)[0]
        if self._survey is None:
            assert self.options is not None
            self._survey = get_survey(
                geoh5=self.geoh5,
                method=self.options.method,
                options=self.options.survey,
            )
        return self._survey

    @property
    def mesh(self):
        self._mesh = self.geoh5.get_entity("mesh")[0]
        if self._mesh is None:
            assert self.options is not None
            self._mesh = get_mesh(
                self.options.method,
                survey=self.survey,
                topography=self.topography,
                options=self.options.mesh,
            )
        return self._mesh

    @property
    def active(self):
        self._active = self.geoh5.get_entity("active_cells")[0]
        if self._active is None:
            self._active = get_active(self.mesh, self.topography)
        return self._active

    @property
    def model(self):
        self._model = self.geoh5.get_entity(self.options.model.name)[0]
        if self._model is None:
            assert self.options is not None
            self._model = get_model(
                method=self.options.method,
                mesh=self.mesh,
                active=self.active.values,
                options=self.options.model,
            )
        return self._model
