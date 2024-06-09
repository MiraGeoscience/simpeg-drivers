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

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import ObjectBase
from simpeg import directives, maps
from simpeg.maps import IdentityMap
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
        self._save_iteration_data_directive = None
        self._save_iteration_residual_directive = None
        self._save_iteration_apparent_resistivity_directive = None
        self._save_iteration_sensitivity_directive = None

    @property
    def beta_estimate_by_eigenvalues_directive(self):
        """"""
        if (
            self.params.initial_beta is None
            and self._beta_estimate_by_eigenvalues_directive is None
        ):
            self._beta_estimate_by_eigenvalues_directive = (
                directives.BetaEstimateMaxDerivative(
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
            "save_iteration_apparent_resistivity_directive",
            # "save_iteration_sensitivity_directive",
        ]:
            if getattr(self, directive) is not None:
                directives_list.append(getattr(self, directive))
        return directives_list

    @property
    def save_iteration_apparent_resistivity_directive(self):
        """"""
        if (
            self._save_iteration_apparent_resistivity_directive is None
            and "direct current" in self.factory_type
        ):
            self._save_iteration_apparent_resistivity_directive = (
                SaveIterationGeoh5Factory(self.params).build(
                    inversion_object=self.driver.inversion_data,
                    active_cells=self.driver.models.active_cells,
                    sorting=np.argsort(np.hstack(self.driver.sorting)),
                    name="Apparent Resistivity",
                )
            )
        return self._save_iteration_apparent_resistivity_directive

    @property
    def save_iteration_data_directive(self):
        """"""
        if self._save_iteration_data_directive is None:
            self._save_iteration_data_directive = SaveIterationGeoh5Factory(
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
            self._save_iteration_model_directive = SaveIterationGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_mesh,
                active_cells=self.driver.models.active_cells,
                save_objective_function=True,
                name="Model",
            )
        return self._save_iteration_model_directive

    @property
    def save_iteration_sensitivity_directive(self):
        """"""
        if self._save_iteration_sensitivity_directive is None:
            self._save_iteration_sensitivity_directive = SaveIterationGeoh5Factory(
                self.params
            ).build(
                inversion_object=self.driver.inversion_mesh,
                active_cells=self.driver.models.active_cells,
                save_objective_function=True,
                name="Sensitivities",
            )
        return self._save_iteration_sensitivity_directive

    @property
    def save_iteration_residual_directive(self):
        """"""
        if (
            self._save_iteration_residual_directive is None
            and self.factory_type not in ["tdem", "fem"]
        ):
            self._save_iteration_residual_directive = SaveIterationGeoh5Factory(
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


class SaveIterationGeoh5Factory(SimPEGFactory):
    def __init__(self, params):
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        return SaveIterationsGeoH5

    def assemble_arguments(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        save_objective_function=False,
        global_misfit=None,
        name=None,
    ):
        return [inversion_object.entity]

    def assemble_keyword_arguments(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        save_objective_function=False,
        global_misfit=None,
        name=None,
    ):
        object_type = "mesh" if hasattr(inversion_object, "mesh") else "data"

        if object_type == "data":
            if self.factory_type in ["magnetotellurics", "tipper"]:
                kwargs = self.assemble_data_keywords_naturalsource(
                    inversion_object=inversion_object,
                    active_cells=active_cells,
                    sorting=sorting,
                    ordering=ordering,
                    transform=transform,
                    save_objective_function=save_objective_function,
                    global_misfit=global_misfit,
                    name=name,
                )

            elif self.factory_type in ["fem", "tdem"]:
                kwargs = self.assemble_data_keywords_em(
                    inversion_object=inversion_object,
                    active_cells=active_cells,
                    sorting=sorting,
                    ordering=ordering,
                    transform=transform,
                    save_objective_function=save_objective_function,
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
                    save_objective_function=save_objective_function,
                    global_misfit=global_misfit,
                    name=name,
                )

            elif self.factory_type in ["gravity", "magnetic scalar", "magnetic vector"]:
                kwargs = self.assemble_data_keywords_potential_fields(
                    inversion_object=inversion_object,
                    active_cells=active_cells,
                    sorting=sorting,
                    transform=transform,
                    save_objective_function=save_objective_function,
                    global_misfit=global_misfit,
                    name=name,
                )
            else:
                return None

            if transform is not None:
                kwargs["transforms"].append(transform)

        else:
            active_cells_map = maps.InjectActiveCells(
                inversion_object.mesh, active_cells, np.nan
            )
            sorting = inversion_object.permutation
            kwargs = {
                "save_objective_function": save_objective_function,
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

            if (
                self.factory_type
                in [
                    "direct current 3d",
                    "direct current 2d",
                    "magnetotellurics",
                    "tipper",
                    "tdem",
                    "fem",
                ]
                and name != "Sensitivities"
            ):
                expmap = maps.ExpMap(inversion_object.mesh)
                kwargs["transforms"] = [expmap * active_cells_map]

            if name == "Sensitivities":
                kwargs["attribute_type"] = "sensitivities"
                kwargs["label"] = "J"

        return kwargs

    @staticmethod
    def assemble_data_keywords_potential_fields(
        inversion_object=None,
        active_cells=None,
        sorting=None,
        transform=None,
        save_objective_function=False,
        global_misfit=None,
        name=None,
    ):
        components = list(inversion_object.observed)
        channels = [None]
        kwargs = {
            "save_objective_function": save_objective_function,
            "attribute_type": "predicted",
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
        save_objective_function=False,
        global_misfit=None,
        name=None,
    ):
        components = list(inversion_object.observed)
        channels = [""]
        is_dc = True if "direct current" in self.factory_type else False
        component = "dc" if is_dc else "ip"
        kwargs = {
            "save_objective_function": save_objective_function,
            "attribute_type": "predicted",
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
                inversion_object.transformations["apparent resistivity"][
                    np.argsort(sorting)
                ],
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

    def assemble_data_keywords_naturalsource(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        save_objective_function=False,
        global_misfit=None,
        name=None,
    ):
        components = list(inversion_object.observed)
        channels = np.unique([list(v) for k, v in inversion_object.observed.items()])

        kwargs = {
            "save_objective_function": save_objective_function,
            "attribute_type": "predicted",
            "data_type": inversion_object.observed_data_types,
            "association": "VERTEX",
            "transforms": [
                np.hstack(
                    [
                        inversion_object.normalizations[chan][comp]
                        for chan in channels
                        for comp in components
                    ]
                )
            ],
            "channels": [f"[{ind}]" for ind in range(len(channels))],
            "components": components,
            "reshape": lambda x: x.reshape((len(channels), len(components), -1)),
        }

        if sorting is not None:
            kwargs["sorting"] = np.hstack(sorting)

        if name == "Residual":
            kwargs["label"] = name
            obs = inversion_object.normalize(inversion_object.observed)
            data = {}
            for f in channels:
                for c in components:
                    data["_".join([str(f), str(c)])] = obs[c][f]

            def natsource_transform(x):
                data_stack = np.row_stack(list(data.values()))
                data_stack = data_stack[:, np.argsort(sorting)]
                return data_stack.ravel() - x

            kwargs.pop("data_type")
            kwargs["transforms"].append(natsource_transform)

        return kwargs

    def assemble_data_keywords_em(
        self,
        inversion_object=None,
        active_cells=None,
        sorting=None,
        ordering=None,
        transform=None,
        save_objective_function=False,
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
            "attribute_type": "predicted",
            "save_objective_function": save_objective_function,
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


class SaveIterationsGeoH5(directives.InversionDirective):
    """
    Saves inversion results to a geoh5 file
    """

    def __init__(self, h5_object, **kwargs):
        self.data_type = {}
        self._association = None
        self.attribute_type = "model"
        self._label = None
        self.channels = [""]
        self.components = [""]
        self._h5_object = None
        self._workspace = None
        self._transforms: list = []
        self.save_objective_function = False
        self.sorting = None
        self._reshape = None
        self.h5_object = h5_object
        self._joint_index = None
        super().__init__(
            inversion=None, dmisfit=None, reg=None, verbose=False, **kwargs
        )

    def initialize(self):
        self.save_components(0)

        if self.save_objective_function:
            self.write_update(0)
            self.save_log()

    def endIter(self):
        self.save_components(self.opt.iter)

        if self.save_objective_function:
            self.write_update(self.opt.iter)
            self.save_log()

    def stack_channels(self, dpred: list):
        """
        Regroup channel values along rows.
        """
        if isinstance(dpred, np.ndarray):
            return self.reshape(dpred)

        return self.reshape(np.hstack(dpred))

    def save_components(
        self, iteration: int, values: list[np.ndarray] = None
    ):  # flake8: noqa
        """
        Sort, transform and store data per components and channels.
        """
        if values is not None:
            prop = self.stack_channels(values)
        elif self.attribute_type == "predicted":
            dpred = getattr(self.invProb, "dpred", None)
            if dpred is None:
                dpred = self.invProb.get_dpred(self.invProb.model)
                self.invProb.dpred = dpred

            if self.joint_index is not None:
                dpred = [dpred[ind] for ind in self.joint_index]

            prop = self.stack_channels(dpred)
        elif self.attribute_type == "sensitivities":
            for directive in self.inversion.directiveList.dList:
                if isinstance(directive, directives.UpdateSensitivityWeights):
                    prop = self.reshape(np.sum(directive.JtJdiag, axis=0) ** 0.5)
        else:
            prop = self.invProb.model

        # Apply transformations
        prop = prop.flatten()
        for fun in self.transforms:
            if isinstance(fun, (IdentityMap, np.ndarray, float)):
                prop = fun * prop
            else:
                prop = fun(prop)

        if prop.ndim == 2:
            prop = prop.T.flatten()

        prop = prop.reshape((len(self.channels), len(self.components), -1))

        with Workspace(self._h5_file) as w_s:
            h5_object = w_s.get_entity(self.h5_object)[0]
            for cc, component in enumerate(self.components):
                if component not in self.data_type:
                    self.data_type[component] = {}

                for ii, channel in enumerate(self.channels):
                    values = prop[ii, cc, :]

                    if self.sorting is not None:
                        values = values[self.sorting]

                    base_name = f"Iteration_{iteration}"
                    if len(component) > 0:
                        base_name += f"_{component}"

                    channel_name = base_name
                    if channel:
                        channel_name += f"_{channel}"

                    if self.label is not None:
                        channel_name += f"_{self.label}"
                        base_name += f"_{self.label}"

                    data = h5_object.add_data(
                        {
                            channel_name: {
                                "association": self.association,
                                "values": values,
                            }
                        }
                    )
                    if channel not in self.data_type[component].keys():
                        self.data_type[component][channel] = data.entity_type
                        type_name = f"{self.attribute_type}_{component}"
                        if channel:
                            type_name += f"_{channel}"
                        data.entity_type.name = type_name
                    else:
                        data.entity_type = w_s.find_type(
                            self.data_type[component][channel].uid,
                            type(self.data_type[component][channel]),
                        )

                    if len(self.channels) > 1 and self.attribute_type == "predicted":
                        h5_object.add_data_to_group(data, base_name)

    def write_update(self, iteration: int):
        """
        Write update to file.
        """
        dirpath = Path(self._h5_file).parent
        filepath = dirpath / "SimPEG.out"

        if iteration == 0:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("iteration beta phi_d phi_m time\n")

        with open(filepath, "a", encoding="utf-8") as f:
            date_time = datetime.now().strftime("%b-%d-%Y:%H:%M:%S")
            f.write(
                f"{iteration} {self.invProb.beta:.3e} {self.invProb.phi_d:.3e} "
                f"{self.invProb.phi_m:.3e} {date_time}\n"
            )

    def save_log(self):
        """
        Save iteration metrics to comments.
        """
        dirpath = Path(self._h5_file).parent

        with Workspace(self._h5_file) as w_s:
            h5_object = w_s.get_entity(self.h5_object)[0]

            for file in ["SimPEG.out", "SimPEG.log"]:
                filepath = dirpath / file

                if not filepath.is_file():
                    continue

                with open(filepath, "rb") as f:
                    raw_file = f.read()

                if h5_object.parent.get_entity(file)[0] is not None:
                    file_entity = h5_object.parent.get_entity(file)[0]
                else:
                    file_entity = h5_object.parent.add_file(filepath)

                file_entity.values = raw_file

    @property
    def joint_index(self):
        """
        Index for joint inversions defining the element in the list of predicted data.
        """
        return self._joint_index

    @joint_index.setter
    def joint_index(self, value: list[int]):
        if not isinstance(value, list):
            raise TypeError("Input 'joint_index' should be a list of int")

        self._joint_index = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value: str):
        assert isinstance(value, str), "'label' must be a string"

        self._label = value

    @property
    def reshape(self):
        """
        Reshape function
        """
        if getattr(self, "_reshape", None) is None:
            self._reshape = lambda x: x.reshape(
                (len(self.channels), len(self.components), -1), order="F"
            )

        return self._reshape

    @reshape.setter
    def reshape(self, fun):
        self._reshape = fun

    @property
    def transforms(self):
        return self._transforms

    @transforms.setter
    def transforms(self, funcs: list):
        if not isinstance(funcs, list):
            funcs = [funcs]

        for fun in funcs:
            if not any(
                [isinstance(fun, (IdentityMap, np.ndarray, float)), callable(fun)]
            ):
                raise TypeError(
                    "Input transformation must be of type"
                    + "SimPEG.maps, numpy.ndarray or callable function"
                )

        self._transforms = funcs

    @property
    def h5_object(self):
        return self._h5_object

    @h5_object.setter
    def h5_object(self, entity: ObjectBase):
        if not isinstance(entity, ObjectBase):
            raise TypeError(
                f"Input entity should be of type {ObjectBase}. {type(entity)} provided"
            )

        self._h5_object = entity.uid
        self._h5_file = entity.workspace.h5file

        if getattr(entity, "n_cells", None) is not None:
            self.association = "CELL"
        else:
            self.association = "VERTEX"

    @property
    def association(self):
        return self._association

    @association.setter
    def association(self, value):
        if not value.upper() in ["CELL", "VERTEX"]:
            raise ValueError(
                f"'association must be one of 'CELL', 'VERTEX'. {value} provided"
            )

        self._association = value.upper()
