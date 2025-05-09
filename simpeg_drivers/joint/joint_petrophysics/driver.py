# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from itertools import combinations

import numpy as np
from geoh5py.groups.property_group_type import GroupTypeEnum
from geoh5py.shared.utils import fetch_active_workspace
from simpeg import directives, maps, utils
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import PGI

from simpeg_drivers.components.factories import (
    DirectivesFactory,
    SaveModelGeoh5Factory,
)
from simpeg_drivers.joint.driver import BaseJointDriver

from .options import JointPetrophysicsOptions


class JointPetrophysicsDriver(BaseJointDriver):
    _options_class = JointPetrophysicsOptions
    _validations = None

    def __init__(self, params: JointPetrophysicsOptions):
        self._wires = None
        self._directives = None
        self._gaussian_model = None

        super().__init__(params)

        with fetch_active_workspace(self.workspace, mode="r+"):
            self.initialize()

    def get_regularization(self):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """
        regularizations = super().get_regularization()
        reg_list, multipliers = self._overload_regularization(regularizations)
        wires = [(f"m{ind}", proj) for ind, proj in enumerate(self.mapping)]
        reg_list.append(
            PGI(
                gmmref=self.gaussian_model,
                mesh=self.inversion_mesh.mesh,
                active_cells=self.models.active_cells,
                wiresmap=maps.Wires(*wires),
                alpha_pgi=1.0,
                alpha_x=1.0,
                alpha_y=1.0,
                alpha_z=1.0,
                reference_model=self.models.reference,
            )
        )
        # TODO: Assign value from UIjson
        multipliers.append(1.0)

        return ComboObjectiveFunction(objfcts=reg_list, multipliers=multipliers)

    @property
    def gaussian_model(self):
        """Gaussian mixture model."""
        if self._gaussian_model is None:
            self._gaussian_model = utils.WeightedGaussianMixture(
                n_components=len(
                    self.geo_units
                ),  # number of rock units: bckgrd, PK, HK
                mesh=self.inversion_mesh.mesh,  # inversion mesh
                actv=self.models.active_cells,  # actv cells
                covariance_type="diag",  # diagonal covariances
            )
            rng = np.random.default_rng(seed=518936)
            rand_model = rng.normal(size=(self.models.n_active, self.n_units))
            self._gaussian_model.fit(rand_model)

            # TODO: Use the corresponding data_maps from the reference data
            #  when available to define the means and covariances and weights
            self._gaussian_model.means_ = self.means
            # set phys. prop covariances for each unit
            self._gaussian_model.covariances_ = self.covariances
            # set global proportions; low-impact as long as not 0 or 1 (total=1)
            self._gaussian_model.weights_ = self.weights

            # important after setting cov. manually: compute precision matrices and cholesky
            self._gaussian_model.compute_clusters_precisions()

        return self._gaussian_model

    @property
    def n_units(self) -> int:
        """Number of model units."""
        return len(self.geo_units)

    @property
    def geo_units(self) -> dict:
        """Model units."""
        units = np.unique(self.models.petrophysics)
        model_map = {
            unit: self.params.petrophysics_model.entity_type.value_map()[unit]
            for unit in units
            if unit != 0
        }

        return model_map

    @property
    def means(self) -> np.ndarray:
        """
        Means of the Gaussian mixture model.

        TODO: Set the means based on the model units when made available.
        """
        means = []
        for mapping in self.mapping:
            model_vec = mapping @ self.models.starting
            unit_mean = []
            for uid in self.geo_units:
                unit_ind = self.models.petrophysics == uid
                start_values = np.mean(model_vec[unit_ind])
                unit_mean.append(start_values)

            means.append(np.r_[unit_mean])
        return self.gaussian_model.means_

    @property
    def covariances(self) -> np.ndarray:
        """
        Covariances of the Gaussian mixture model.

        TODO: Set the covariances based on the model units when made available.
        """
        return np.ones((self.n_units, len(self.drivers)))

    @property
    def weights(self) -> np.ndarray:
        """
        Weights of the Gaussian mixture model.

        TODO: Set the weights based on the model units when made available.
        """
        return np.ones(self.n_units)
