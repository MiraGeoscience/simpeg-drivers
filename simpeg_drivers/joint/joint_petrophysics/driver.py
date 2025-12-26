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
    _params_class = JointPetrophysicsOptions

    def __init__(self, params: JointPetrophysicsOptions):
        self._wires = None
        self._class_mapping: np.ndarray | None = None
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

                # TODO: To bring back once we let the classification change
                # directives_list.append(
                #     directives.SavePGIModel(
                #         self.inversion_mesh.entity,
                #         self.pgi_regularization,
                #         self.geo_units,
                #         [driver.params.physical_property for driver in self.drivers],
                #         transforms=[
                #             lambda x: np.r_[list(self.geo_units)][self.class_mapping][
                #                 x.astype(int)
                #             ],
                #             maps.InjectActiveCells(
                #                 self.inversion_mesh.mesh, self.models.active_cells, 0
                #             ),
                #         ],
                #         reference_type=self.params.models.petrophysical_model.entity_type,
                #     )
                # )
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

                DirectivesFactory.configure_save_directives(
                    self._directives.directive_list
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
        multipliers.append(self.params.models.alpha_s)

        return ComboObjectiveFunction(objfcts=reg_list, multipliers=multipliers)

    @property
    def gaussian_model(self):
        """Gaussian mixture model."""
        if self._gaussian_model is None:
            self._gaussian_model = utils.WeightedGaussianMixture(
                n_components=len(self.geo_units),
                mesh=self.inversion_mesh.mesh,
                actv=self.models.active_cells,
                covariance_type="diag",
                random_state=1,
            )
            # TODO: Use the corresponding data_maps from the reference data
            #  when available to define the means and covariances and weights
            self._gaussian_model.means_ = self.means[self.class_mapping]
            # set phys. prop covariances for each unit
            self._gaussian_model.covariances_ = self.covariances[self.class_mapping]
            # set global proportions; low-impact as long as not 0 or 1 (total=1)
            self._gaussian_model.weights_ = self.weights[self.class_mapping]

            # important after setting cov. manually: compute precision matrices and cholesky
            self._gaussian_model.compute_clusters_precisions()

        return self._gaussian_model

    @property
    def class_mapping(self) -> dict:
        """Mapping of model units to geophysical properties."""
        if getattr(self, "_class_mapping", None) is None:
            self._class_mapping = np.argsort(self.weights)[::-1]

        return self._class_mapping

    @property
    def n_units(self) -> int:
        """Number of model units."""
        return len(self.geo_units)

    @property
    def geo_units(self) -> dict:
        """Model units."""
        units = np.unique(self.models.petrophysical_model)
        model_map = {
            unit: self.params.models.petrophysical_model.entity_type.value_map()[unit]
            for unit in units
            if unit != 0
        }

        return model_map

    @property
    def membership(self) -> np.ndarray[np.int]:
        if self._membership is None:
            self._membership = np.empty(self.models.n_active, dtype=int)
            for ii, unit in enumerate(self.geo_units):
                unit_ind = self.models.petrophysical_model == unit
                self._membership[unit_ind] = self.class_mapping[ii]

        return self._membership

    @property
    def means(self) -> np.ndarray:
        """
        Means of the Gaussian mixture model.

        TODO: Set the means based on the model units when made available.
        """
        means = []
        for mapping in self.mapping:
            model_vec = mapping @ self.models.reference_model
            unit_mean = []
            for uid in self.geo_units:
                unit_ind = self.models.petrophysical_model == uid
                start_values = np.mean(model_vec[unit_ind])
                unit_mean.append(start_values)

            means.append(np.c_[unit_mean])

        return np.hstack(means)

    @property
    def covariances(self) -> np.ndarray:
        """
        Covariances of the Gaussian mixture model.

        TODO: Set the covariances based on the model units when made available.
        """
        return np.ones((self.n_units, len(self.mapping)))

    @property
    def weights(self) -> np.ndarray:
        """
        Weights of the Gaussian mixture model.

        TODO: Set the weights based on the model units when made available.
        """
        weights = []
        volumes = self.inversion_mesh.mesh.cell_volumes[self.models.active_cells]
        for uid in self.geo_units:
            weights.append(volumes[self.models.petrophysical_model == uid].sum())
        return np.r_[weights] / np.sum(weights)

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
                reference_model=self.models.reference_model,
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
