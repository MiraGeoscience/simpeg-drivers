# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=W0613
# pylint: disable=W0221

from __future__ import annotations

from abc import ABC
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from geoh5py.groups.property_group import GroupTypeEnum
from numpy import sqrt
from simpeg import directives, maps
from simpeg.utils.mat_utils import cartesian2amplitude_dip_azimuth

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.options import BaseInversionOptions


if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver

logger = getLogger(__name__)


class DirectivesFactory:
    def __init__(self, driver: InversionDriver):
        self.driver = driver
        self.params = driver.params
        self.factory_type = self.driver.params.inversion_type
        self._directive_list: list[directives.InversionDirective] | None = None
        self._vector_inversion_directive = None
        self._update_sensitivity_weights_directive = None
        self._update_irls_directive = None
        self._beta_estimate_by_eigenvalues_directive = None
        self._update_preconditioner_directive = None
        self._save_iteration_model_directive = None
        self._save_property_group = None
        self._save_sensitivities_directive = None
        self._save_iteration_data_directive = None
        self._save_iteration_residual_directive = None
        self._save_iteration_log_files = None
        self._save_iteration_apparent_resistivity_directive = None
        self._scale_misfits = None

    @staticmethod
    def configure_save_directives(directives_list):
        """
        Find all SaveGeoH5 directives in the list and set their open_geoh5 and
        close_geoh5 flags such that the first and last directive handles the
        opening and closing of the target geoh5.

        :param directives_list: List of directives to configure.
        """
        save_dirs = []
        for directive in directives_list:
            if isinstance(directive, directives.BaseSaveGeoH5):
                directive.close_geoh5 = False
                directive.open_geoh5 = False
                save_dirs.append(directive)

        save_dirs[0].open_geoh5 = True
        save_dirs[-1].close_geoh5 = True

    @property
    def beta_estimate_by_eigenvalues_directive(self):
        """"""
        if (
            self.params.cooling_schedule.initial_beta is None
            and self._beta_estimate_by_eigenvalues_directive is None
        ):
            self._beta_estimate_by_eigenvalues_directive = (
                directives.BetaEstimateDerivative(
                    beta0_ratio=self.params.cooling_schedule.initial_beta_ratio,
                    random_seed=0,
                )
            )

        return self._beta_estimate_by_eigenvalues_directive

    @property
    def directive_list(self):
        """List of directives to be used in inversion."""
        if self._directive_list is None:
            if not self.params.forward_only:
                self._directive_list = self.inversion_directives + self.save_directives
            else:
                self._directive_list = self.save_directives

            self.configure_save_directives(self._directive_list)

        return self._directive_list

    @directive_list.setter
    def directive_list(self, value):
        if not all(
            isinstance(directive, directives.InversionDirective) for directive in value
        ):
            raise TypeError(
                "All directives must be of type SimPEG.directives.InversionDirective"
            )

        self._directive_list = value

    @property
    def inversion_directives(self):
        """List of directives that control the inverse."""
        directives_list = []
        for directive in [
            "vector_inversion_directive",
            "update_irls_directive",
            "update_sensitivity_weights_directive",
            "beta_estimate_by_eigenvalues_directive",
            "update_preconditioner_directive",
            "scale_misfits",
        ]:
            if getattr(self, directive) is not None:
                directives_list.append(getattr(self, directive))
        return directives_list

    @property
    def save_directives(self):
        """List of directives to save iteration data and models."""
        directives_list = []
        for directive in [
            "save_iteration_model_directive",
            "save_iteration_data_directive",
            "save_iteration_residual_directive",
            "save_sensitivities_directive",
            "save_property_group",
            "save_iteration_log_files",
            "save_iteration_apparent_resistivity_directive",
        ]:
            save_directive = getattr(self, directive)
            if save_directive is not None:
                directives_list.append(getattr(self, directive))

                if (
                    isinstance(save_directive, directives.SaveDataGeoH5)
                    and len(save_directive.channels) > 1
                ):
                    save_group = directives.SavePropertyGroup(
                        self.driver.inversion_data.entity,
                        channels=save_directive.channels,
                        components=save_directive.components,
                    )
                    directives_list.append(save_group)

                if (
                    isinstance(save_directive, directives.SaveModelGeoH5)
                    and not self.params.forward_only
                ):
                    save_model_group = directives.SaveLPModelGroup(
                        self.driver.inversion_mesh.entity,
                        self.driver.directives.update_irls_directive,
                    )
                    directives_list.append(save_model_group)

        return directives_list

    @property
    def save_iteration_apparent_resistivity_directive(self):
        """"""
        if (
            self._save_iteration_apparent_resistivity_directive is None
            and "direct current" in self.factory_type
        ):
            self._save_iteration_apparent_resistivity_directive = SaveDataGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_data,
                name="Apparent Resistivity",
            )
        return self._save_iteration_apparent_resistivity_directive

    @property
    def save_property_group(self):
        if (
            self._save_property_group is None
            and self.params.inversion_type == "magnetic vector"
        ):
            self._save_property_group = directives.SavePropertyGroup(
                self.driver.inversion_mesh.entity,
                group_type=GroupTypeEnum.DIPDIR,
                channels=["declination", "inclination"],
            )
        return self._save_property_group

    @property
    def save_sensitivities_directive(self):
        """"""
        if self._save_sensitivities_directive is None and isinstance(
            self.params, BaseInversionOptions
        ):
            self._save_sensitivities_directive = SaveSensitivitiesGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_mesh,
                active_cells=self.driver.models.active_cells,
                global_misfit=self.driver.data_misfit,
                name="Sensitivities",
            )
        return self._save_sensitivities_directive

    @property
    def save_iteration_data_directive(self):
        """"""
        if self._save_iteration_data_directive is None:
            self._save_iteration_data_directive = SaveDataGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_data,
                name="Data",
            )
        return self._save_iteration_data_directive

    @property
    def save_iteration_model_directive(self):
        """"""
        if self._save_iteration_model_directive is None:
            model_directive = SaveModelGeoh5Factory(self.params).build(
                inversion_object=self.driver.inversion_mesh,
                active_cells=self.driver.models.active_cells,
                name="Model",
            )
            self._save_iteration_model_directive = model_directive

        return self._save_iteration_model_directive

    @property
    def save_iteration_log_files(self):
        """"""
        if self._save_iteration_log_files is None and self.driver.logger:
            self._save_iteration_log_files = directives.SaveLogFilesGeoH5(
                self.driver.out_group,
            )
        return self._save_iteration_log_files

    @property
    def save_iteration_residual_directive(self):
        """"""
        if (
            self._save_iteration_residual_directive is None
            and self.factory_type
            not in ["tdem", "tdem 1d", "fdem", "fdem 1d", "magnetotellurics", "tipper"]
        ):
            self._save_iteration_residual_directive = SaveDataGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_data,
                name="Residual",
            )
        return self._save_iteration_residual_directive

    @property
    def scale_misfits(self):
        if (
            self._scale_misfits is None
            and self.params.directives.auto_scale_misfits
            and len(self.driver.data_misfit.objfcts) > 1
        ):
            self._scale_misfits = directives.ScaleMisfitMultipliers(
                self.params.geoh5.h5file.parent
            )
        return self._scale_misfits

    @property
    def update_irls_directive(self):
        """Directive to update IRLS."""
        if self._update_irls_directive is None:
            finite_data_count, total_data_count = self.driver.count_data()
            rescale = finite_data_count / total_data_count
            chi_factor = self.params.cooling_schedule.chi_factor * rescale

            starting_chi_factor = self.params.irls.starting_chi_factor
            if starting_chi_factor is not None:
                starting_chi_factor *= rescale
                if chi_factor > starting_chi_factor:
                    logger.warning(
                        "Starting chi factor is greater than target chi factor.\n"
                        "Setting the target chi factor to the starting chi factor."
                    )
                    starting_chi_factor = chi_factor

            self._update_irls_directive = directives.UpdateIRLS(
                f_min_change=self.params.optimization.f_min_change,
                max_irls_iterations=self.params.irls.max_irls_iterations,
                misfit_tolerance=self.params.irls.beta_tol,
                percentile=self.params.irls.percentile,
                cooling_rate=self.params.cooling_schedule.cooling_rate,
                cooling_factor=self.params.cooling_schedule.cooling_factor,
                irls_cooling_factor=self.params.irls.epsilon_cooling_factor,
                chifact_start=starting_chi_factor or chi_factor,
                chifact_target=chi_factor,
            )
        return self._update_irls_directive

    @property
    def update_preconditioner_directive(self):
        """"""
        if self._update_preconditioner_directive is None:
            self._update_preconditioner_directive = directives.UpdatePreconditioner()

        return self._update_preconditioner_directive

    @property
    def update_sensitivity_weights_directive(self):
        if self._update_sensitivity_weights_directive is None:
            self._update_sensitivity_weights_directive = (
                directives.UpdateSensitivityWeights(
                    every_iteration=self.params.directives.every_iteration_bool,
                    threshold_value=self.params.directives.sens_wts_threshold / 100.0,
                )
            )

        return self._update_sensitivity_weights_directive

    @property
    def vector_inversion_directive(self):
        """Directive to update vector model."""
        if self._vector_inversion_directive is None and "vector" in self.factory_type:
            reference_angles = (
                getattr(self.driver.params.models, "reference_model", None) is not None,
                getattr(self.driver.params.models, "reference_inclination", None)
                is not None,
                getattr(self.driver.params.models, "reference_declination", None)
                is not None,
            )

            self._vector_inversion_directive = directives.VectorInversion(
                self.driver.data_misfit.objfcts,
                self.driver.regularization,
                chifact_target=self.driver.params.cooling_schedule.chi_factor * 2,
                reference_angles=reference_angles,
            )
        return self._vector_inversion_directive


class SaveGeoh5Factory(SimPEGFactory, ABC):
    _concrete_object = None

    def __init__(self, params):
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        return self._concrete_object

    def assemble_arguments(
        self,
        inversion_object=None,
        active_cells=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        return [inversion_object.entity]


class SaveModelGeoh5Factory(SaveGeoh5Factory):
    """
    Factory to create a SaveModelGeoH5 directive.
    """

    _concrete_object = directives.SaveModelGeoH5

    def assemble_keyword_arguments(
        self,
        inversion_object=None,
        active_cells=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        active_cells_map = maps.InjectActiveCells(
            inversion_object.mesh, active_cells, np.nan
        )
        kwargs = {
            "label": "model",
            "association": "CEll",
            "transforms": [active_cells_map, inversion_object.permutation.T],
        }

        if self.factory_type == "magnetic vector":
            kwargs["channels"] = ["amplitude", "inclination", "declination"]
            kwargs["transforms"] = [
                cartesian2amplitude_dip_azimuth,
                active_cells_map,
                inversion_object.permutation.T,
            ]

        if self.factory_type in [
            "direct current 3d",
            "direct current 2d",
            "magnetotellurics",
            "tipper",
            "tdem",
            "tdem 1d",
            "fdem",
            "fdem 1d",
        ]:
            expmap = maps.ExpMap(inversion_object.mesh)
            kwargs["transforms"] = [
                expmap * active_cells_map,
                inversion_object.permutation.T,
            ]

            if self.params.models.model_type == "Resistivity (Ohm-m)":
                kwargs["transforms"].append(lambda x: 1 / x)

        if "1d" in self.factory_type:
            ghosts = (
                np.squeeze(np.asarray(inversion_object.permutation.sum(axis=0))) == 0
            )
            nn_vals = np.ones_like(ghosts, dtype=float)
            nn_vals[ghosts] = np.nan
            kwargs["transforms"].append(lambda x: nn_vals * x)

        return kwargs


class SaveSensitivitiesGeoh5Factory(SaveGeoh5Factory):
    """
    Factory to create a SaveModelGeoH5 directive.
    """

    _concrete_object = directives.SaveSensitivityGeoH5

    def assemble_keyword_arguments(
        self,
        inversion_object=None,
        active_cells=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        active_cells_map = maps.InjectActiveCells(
            inversion_object.mesh, active_cells, np.nan
        )

        def volume_normalization(val):
            return val / inversion_object.mesh.cell_volumes

        kwargs = {
            "label": "model",
            "association": "CEll",
            "dmisfit": global_misfit,
            "transforms": [
                active_cells_map,
                sqrt,
                volume_normalization,
                inversion_object.permutation.T,
            ],
        }

        if self.factory_type == "magnetic vector":
            kwargs["channels"] = [None]
            kwargs["transforms"] = [
                lambda x: x.reshape((-1, 3), order="F"),
                lambda x: np.linalg.norm(x, axis=1),
            ] + kwargs["transforms"]

        kwargs["label"] = "sensitivities"

        return kwargs


class SaveDataGeoh5Factory(SaveGeoh5Factory):
    """
    Factory to create a SaveDataGeoH5 directive.
    """

    _concrete_object = directives.SaveDataGeoH5

    def assemble_keyword_arguments(
        self,
        inversion_object=None,
        name=None,
    ):
        receivers = inversion_object.entity
        channels = getattr(receivers, "channels", [None])
        components = list(inversion_object.observed)
        ordering = inversion_object.survey.ordering
        n_locations = len(np.unique(ordering[:, 2]))

        def reshape(values):
            data = np.zeros((len(channels), len(components), n_locations))
            data[ordering[:, 0], ordering[:, 1], ordering[:, 2]] = values
            return data

        kwargs = {
            "data_type": inversion_object.observed_data_types,
            "association": "VERTEX",
            "transforms": [
                np.hstack(
                    [
                        1 / inversion_object.normalizations[chan][comp]
                        for chan in channels
                        for comp in components
                    ],
                ),
            ],
            "channels": channels,
            "components": components,
            "reshape": reshape,
        }

        if self.factory_type in [
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
        ]:
            kwargs = self.assemble_data_keywords_dcip(
                inversion_object=inversion_object, name=name, **kwargs
            )

        elif self.factory_type in ["gravity", "magnetic scalar", "magnetic vector"]:
            kwargs = self.assemble_data_keywords_potential_fields(
                inversion_object=inversion_object,
                name=name,
                **kwargs,
            )

        return kwargs

    @staticmethod
    def assemble_data_keywords_potential_fields(
        inversion_object=None,
        name=None,
        **kwargs,
    ):
        if name == "Residual":
            kwargs["label"] = name
            data = inversion_object.normalize(inversion_object.observed)

            def potfield_transform(x):
                data_stack = np.vstack([k[None] for k in data.values()])
                return data_stack.ravel() - x

            kwargs.pop("data_type")
            kwargs["transforms"].append(potfield_transform)

        return kwargs

    def assemble_data_keywords_dcip(
        self,
        inversion_object=None,
        name=None,
        **kwargs,
    ):
        components = list(inversion_object.observed)
        kwargs["association"] = "CELL"

        if "direct current" in self.factory_type and name == "Apparent Resistivity":
            kwargs["transforms"].insert(
                0,
                inversion_object.survey.apparent_resistivity,
            )
            kwargs["channels"] = ["apparent_resistivity"]
            observed = self.params.geoh5.get_entity("Observed_apparent_resistivity")[0]
            if observed is not None:
                kwargs["data_type"] = {
                    components[0]: {"apparent_resistivity": observed.entity_type}
                }

        if name == "Residual":
            kwargs["label"] = name
            data = inversion_object.normalize(inversion_object.observed)

            def dcip_transform(x):
                data_stack = np.vstack([k[None] for k in data.values()])
                return data_stack.ravel() - x

            kwargs["transforms"].insert(0, dcip_transform)
            kwargs.pop("data_type")

        return kwargs
