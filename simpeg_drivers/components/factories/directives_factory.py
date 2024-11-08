# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=W0613
# pylint: disable=W0221

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import numpy as np
from geoh5py.groups.property_group import GroupTypeEnum
from simpeg import directives, maps
from simpeg.utils.mat_utils import cartesian2amplitude_dip_azimuth

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver


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

    @property
    def beta_estimate_by_eigenvalues_directive(self):
        """"""
        if (
            self.params.initial_beta is None
            and self._beta_estimate_by_eigenvalues_directive is None
        ):
            self._beta_estimate_by_eigenvalues_directive = (
                directives.BetaEstimateDerivative(
                    beta0_ratio=self.params.initial_beta_ratio, seed=0
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
                active_cells=self.driver.models.active_cells,
                sorting=np.argsort(np.hstack(self.driver.sorting)),
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
        if (
            self._save_sensitivities_directive is None
            and self.params.save_sensitivities
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
                active_cells=self.driver.models.active_cells,
                sorting=np.argsort(np.hstack(self.driver.sorting)),
                ordering=self.driver.ordering,
                global_misfit=self.driver.data_misfit,
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
        if self._save_iteration_log_files is None:
            self._save_iteration_log_files = directives.SaveLogFilesGeoH5(
                self.driver.out_group,
            )
        return self._save_iteration_log_files

    @property
    def save_iteration_residual_directive(self):
        """"""
        if (
            self._save_iteration_residual_directive is None
            and self.factory_type not in ["tdem", "fem", "magnetotellurics", "tipper"]
        ):
            self._save_iteration_residual_directive = SaveDataGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_data,
                active_cells=self.driver.models.active_cells,
                sorting=np.argsort(np.hstack(self.driver.sorting)),
                ordering=self.driver.ordering,
                name="Residual",
            )
        return self._save_iteration_residual_directive

    @property
    def scale_misfits(self):
        if (
            self._scale_misfits is None
            and self.params.auto_scale_misfits
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
            has_chi_start = self.params.starting_chi_factor is not None
            self._update_irls_directive = directives.Update_IRLS(
                f_min_change=self.params.f_min_change,
                max_irls_iterations=self.params.max_irls_iterations,
                max_beta_iterations=self.params.max_global_iterations,
                beta_tol=self.params.beta_tol,
                prctile=self.params.prctile,
                coolingRate=self.params.coolingRate,
                coolingFactor=self.params.coolingFactor,
                coolEps_q=self.params.coolEps_q,
                coolEpsFact=self.params.coolEpsFact,
                beta_search=self.params.beta_search,
                chifact_start=(
                    self.params.starting_chi_factor
                    if has_chi_start
                    else self.params.chi_factor
                ),
                chifact_target=self.params.chi_factor,
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
                    every_iteration=self.params.every_iteration_bool,
                    threshold_value=self.params.sens_wts_threshold / 100.0,
                )
            )

        return self._update_sensitivity_weights_directive

    @property
    def vector_inversion_directive(self):
        """Directive to update vector model."""
        if self._vector_inversion_directive is None and "vector" in self.factory_type:
            reference_angles = (
                getattr(self.driver.params, "reference_model", None) is not None,
                getattr(self.driver.params, "reference_inclination", None) is not None,
                getattr(self.driver.params, "reference_declination", None) is not None,
            )

            self._vector_inversion_directive = directives.VectorInversion(
                [objective.simulation for objective in self.driver.data_misfit.objfcts],
                self.driver.regularization,
                chifact_target=self.driver.params.chi_factor * 2,
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
        sorting=None,
        ordering=None,
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
        sorting=None,
        ordering=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        active_cells_map = maps.InjectActiveCells(
            inversion_object.mesh, active_cells, np.nan
        )
        sorting = inversion_object.permutation
        kwargs = {
            "label": "model",
            "association": "CEll",
            "transforms": [active_cells_map],
            "sorting": sorting,
        }

        if self.factory_type == "magnetic vector":
            kwargs["channels"] = ["amplitude", "inclination", "declination"]
            kwargs["transforms"] = [
                cartesian2amplitude_dip_azimuth,
                active_cells_map,
            ]

        if self.factory_type in [
            "direct current 3d",
            "direct current 2d",
            "magnetotellurics",
            "tipper",
            "tdem",
            "fem",
        ]:
            expmap = maps.ExpMap(inversion_object.mesh)
            kwargs["transforms"] = [expmap * active_cells_map]

            if self.params.model_type == "Resistivity (Ohm-m)":
                kwargs["transforms"].append(lambda x: 1 / x)
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
        sorting=None,
        ordering=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        active_cells_map = maps.InjectActiveCells(
            inversion_object.mesh, active_cells, np.nan
        )
        sorting = inversion_object.permutation
        kwargs = {
            "label": "model",
            "association": "CEll",
            "dmisfit": global_misfit,
            "transforms": [active_cells_map],
            "sorting": sorting,
        }

        if self.factory_type == "magnetic vector":
            kwargs["channels"] = ["amplitude", "inclination", "declination"]
            kwargs["transforms"] = [
                active_cells_map,
            ]

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
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        if self.factory_type in ["fem", "tdem", "magnetotellurics", "tipper"]:
            kwargs = self.assemble_data_keywords_em(
                inversion_object=inversion_object,
                active_cells=active_cells,
                sorting=sorting,
                ordering=ordering,
                transform=transform,
                global_misfit=global_misfit,
                name=name,
            )

        elif self.factory_type in [
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
        ]:
            kwargs = self.assemble_data_keywords_dcip(
                inversion_object=inversion_object,
                active_cells=active_cells,
                sorting=sorting,
                transform=transform,
                global_misfit=global_misfit,
                name=name,
            )

        elif self.factory_type in ["gravity", "magnetic scalar", "magnetic vector"]:
            kwargs = self.assemble_data_keywords_potential_fields(
                inversion_object=inversion_object,
                active_cells=active_cells,
                sorting=sorting,
                transform=transform,
                global_misfit=global_misfit,
                name=name,
            )
        else:
            return None

        if transform is not None:
            kwargs["transforms"].append(transform)

        return kwargs

    @staticmethod
    def assemble_data_keywords_potential_fields(
        inversion_object=None,
        active_cells=None,
        sorting=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        components = list(inversion_object.observed)
        channels = [None]
        kwargs = {
            "data_type": {
                comp: {channel: dtype for channel in channels}
                for comp, dtype in inversion_object.observed_data_types.items()
            },
            "transforms": [
                np.hstack(
                    [
                        inversion_object.normalizations[chan][comp]
                        for chan in channels
                        for comp in components
                    ]
                )
            ],
            "channels": channels,
            "components": components,
            "association": "VERTEX",
            "reshape": lambda x: x.reshape(
                (len(channels), len(components), -1), order="F"
            ),
        }

        if sorting is not None:
            kwargs["sorting"] = np.hstack(sorting)

        if name == "Residual":
            kwargs["label"] = name
            data = inversion_object.normalize(inversion_object.observed)

            def potfield_transform(x):
                data_stack = np.row_stack(list(data.values()))
                data_stack = data_stack[:, np.argsort(sorting)]
                return data_stack.ravel() - x

            kwargs.pop("data_type")
            kwargs["transforms"].append(potfield_transform)

        return kwargs

    def assemble_data_keywords_dcip(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        components = list(inversion_object.observed)
        channels = [""]
        is_dc = True if "direct current" in self.factory_type else False
        component = "dc" if is_dc else "ip"
        kwargs = {
            "data_type": {
                comp: {channel: dtype for channel in channels}
                for comp, dtype in inversion_object.observed_data_types.items()
            },
            "transforms": [
                np.hstack(
                    [inversion_object.normalizations[None][c] for c in components]
                )
            ],
            "channels": channels,
            "components": [component],
            "reshape": lambda x: x.reshape(
                (len(channels), len(components), -1), order="F"
            ),
            "association": "CELL",
        }

        if sorting is not None:
            kwargs["sorting"] = np.hstack(sorting)

        if is_dc and name == "Apparent Resistivity":
            kwargs["transforms"].insert(
                0,
                inversion_object.survey.apparent_resistivity[np.argsort(sorting)],
            )
            kwargs["channels"] = ["apparent_resistivity"]
            observed = self.params.geoh5.get_entity("Observed_apparent_resistivity")[0]
            if observed is not None:
                kwargs["data_type"] = {
                    component: {"apparent_resistivity": observed.entity_type}
                }

        if name == "Residual":
            kwargs["label"] = name
            data = inversion_object.normalize(inversion_object.observed)

            def dcip_transform(x):
                data_stack = np.row_stack(list(data.values())).ravel()
                sorting_stack = np.tile(np.argsort(sorting), len(data))
                return data_stack[sorting_stack] - x

            kwargs["transforms"].insert(0, dcip_transform)
            kwargs.pop("data_type")

        return kwargs

    def assemble_data_keywords_em(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        global_misfit=None,
        name=None,
    ):
        receivers = inversion_object.entity
        channels = np.array(receivers.channels, dtype=float)
        components = list(inversion_object.observed)
        ordering = np.vstack(ordering)
        channel_ids = ordering[:, 0]
        component_ids = ordering[:, 1]
        rx_ids = ordering[:, 2]

        def reshape(values):
            data = np.zeros((len(channels), len(components), receivers.n_vertices))
            data[channel_ids, component_ids, rx_ids] = values
            return data

        kwargs = {
            "data_type": inversion_object.observed_data_types,
            "association": "VERTEX",
            "transforms": np.hstack(
                [
                    1 / inversion_object.normalizations[chan][comp]
                    for chan in channels
                    for comp in components
                ]
            ),
            "channels": [f"[{ind}]" for ind, _ in enumerate(channels)],
            "components": components,
            "sorting": sorting,
            "_reshape": reshape,
        }

        return kwargs
