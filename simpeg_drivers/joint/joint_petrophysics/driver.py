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
from simpeg.regularization.pgi import PGIsmallness

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
        self._membership: np.ndarray = None
        self._gaussian_model = None
        self._pgi_regularization: PGIsmallness | None = None

        super().__init__(params)

        with fetch_active_workspace(self.workspace, mode="r+"):
            self.initialize()

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None and not self.params.forward_only:
            with fetch_active_workspace(self.workspace, mode="r+"):
                directives_list = self._get_drivers_directives()
                directives_list.append(
                    directives.PGI_UpdateParameters(
                        update_gmm=True,
                        kappa=0.0,
                        fixed_membership=np.c_[
                            np.arange(self.models.n_active), self.membership
                        ],
                    )
                )
                directives_list += self._get_global_model_save_directives()
                directives_list.append(
                    directives.SavePGIModel(
                        self.inversion_mesh.entity,
                        self.pgi_regularization,
                        self.geo_units,
                        [driver.params.physical_property for driver in self.drivers],
                        transforms=[
                            maps.InjectActiveCells(
                                self.inversion_mesh.mesh, self.models.active_cells, 0
                            )
                        ],
                        value_map=self.params.petrophysics_model.entity_type.value_map,
                    )
                )
                directives_list.append(
                    directives.SaveLPModelGroup(
                        self.inversion_mesh.entity,
                        self._directives.update_irls_directive,
                    )
                )
                directives_list.append(self._directives.save_iteration_log_files)
                self._directives.directive_list = (
                    self._directives.inversion_directives + directives_list
                )
        return self._directives

    def get_regularization(self):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """
        regularizations = super().get_regularization()
        reg_list, multipliers = self._overload_regularization(regularizations)
        reg_list.append(self.pgi_regularization)
        # TODO: Assign value from UIjson
        multipliers.append(self.params.alpha_s)

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
            rand_model = rng.normal(size=(self.models.n_active, len(self.mapping)))
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
    def membership(self) -> np.ndarray[np.int]:
        if self._membership is None:
            self._membership = np.zeros(self.models.n_active, dtype=int)
            for ii, unit in enumerate(self.geo_units):
                unit_ind = self.models.petrophysics == unit
                self._membership[unit_ind] = ii

        return self._membership

    @property
    def means(self) -> np.ndarray:
        """
        Means of the Gaussian mixture model.

        TODO: Set the means based on the model units when made available.
        """
        means = []
        for mapping in self.mapping:
            model_vec = mapping @ self.models.reference
            unit_mean = []
            for uid in self.geo_units:
                unit_ind = self.models.petrophysics == uid
                start_values = np.mean(model_vec[unit_ind])
                unit_mean.append(start_values)

            means.append(np.c_[unit_mean])
        self.gaussian_model.means_ = np.hstack(means)

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
        return np.ones(self.n_units) / self.n_units

    @property
    def pgi_regularization(self):
        """
        Create a PGI regularization object for the inversion.
        """
        if self._pgi_regularization is None:
            wires = [(f"m{ind}", proj) for ind, proj in enumerate(self.mapping)]
            maplist = [maps.IdentityMap(nP=self.models.n_active)] * len(self.mapping)
            self._pgi_regularization = PGIsmallness(
                gmmref=self.gaussian_model,
                mesh=self.inversion_mesh.mesh,
                active_cells=self.models.active_cells,
                wiresmap=maps.Wires(*wires),
                maplist=maplist,
                reference_model=self.models.reference,
            )
        return self._pgi_regularization

    def _overload_regularization(self, regularization: ComboObjectiveFunction):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """

        reg_list, multipliers = super()._overload_regularization(regularization)
        for reg in reg_list:
            reg.alpha_s = 0.0

        return reg_list, multipliers
