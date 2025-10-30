# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=unexpected-keyword-arg, no-value-for-parameter

from __future__ import annotations

import sys
from logging import getLogger
from pathlib import Path

import numpy as np
import simpeg.dask.objective_function as dask_objective_function
from geoh5py.groups.property_group_type import GroupTypeEnum
from geoh5py.shared.utils import fetch_active_workspace
from grid_apps.utils import (
    collocate_octrees,
    create_octree_from_octrees,
    treemesh_2_octree,
)
from simpeg import directives
from simpeg.directives import SaveLPModelGroup
from simpeg.maps import Projection, TileMap
from simpeg.objective_function import ComboObjectiveFunction

from simpeg_drivers.components.factories import (
    DirectivesFactory,
    SaveDataGeoh5Factory,
    SaveModelGeoh5Factory,
)
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.utils.utils import simpeg_group_to_driver


logger = getLogger(__name__)


class BaseJointDriver(InversionDriver):
    def __init__(self, params: BaseJointOptions):
        self._directives = None
        self._drivers = None
        self._wires = None

        super().__init__(params)

    @property
    def data_misfit(self):
        if getattr(self, "_data_misfit", None) is None and self.drivers is not None:
            objective_functions = []
            multipliers = []
            for label, driver in zip("abc", self.drivers, strict=False):
                if driver.data_misfit is not None:
                    objective_functions += driver.data_misfit.objfcts

                    for ii, fun in enumerate(driver.data_misfit.objfcts):
                        fun.name = f"Group_{label.upper()}:Tile_{ii}"

                    multipliers += [
                        (getattr(self.params, f"group_{label}_multiplier") or 1.0)
                        ** 2.0
                    ] * len(driver.data_misfit.objfcts)

            if self.client:
                return dask_objective_function.DistributedComboMisfits(
                    objfcts=objective_functions,
                    multipliers=multipliers,
                    client=self.client,
                )

            self._data_misfit = ComboObjectiveFunction(
                objfcts=objective_functions, multipliers=multipliers
            )

        return self._data_misfit

    @property
    def drivers(self) -> list[InversionDriver] | None:
        """List of inversion drivers."""
        if self._drivers is None:
            drivers = []
            # Create sub-drivers
            for group in self.params.groups:
                driver = simpeg_group_to_driver(group, self.workspace)
                new = driver.out_group.copy(
                    copy_children=False, copy_relatives=False, parent=self.out_group
                )
                driver.out_group = new
                drivers.append(driver)

            self._drivers = drivers

        return self._drivers

    def get_local_actives(self, driver: InversionDriver):
        """Get all local active cells within the global mesh for a given driver."""

        in_local = driver.inversion_mesh.mesh.get_containing_cells(
            self.inversion_mesh.mesh.gridCC
        )
        local_actives = driver.inversion_topography.active_cells(
            driver.inversion_mesh, driver.inversion_data
        )
        global_active = local_actives[in_local]
        global_active[
            ~driver.inversion_mesh.mesh.is_inside(self.inversion_mesh.mesh.gridCC)
        ] = False
        return global_active

    def initialize(self):
        """Generate sub drivers."""

        self.validate_create_mesh()

        # Add re-projection to the global mesh
        global_actives = np.zeros(self.inversion_mesh.mesh.nC, dtype=bool)
        for driver in self.drivers:
            local_actives = self.get_local_actives(driver)
            global_actives |= local_actives

        self.models.active_cells = global_actives
        for driver, wire in zip(self.drivers, self.wires, strict=True):
            logger.info("Initializing driver %s", driver.params.name)
            projection = TileMap(
                self.inversion_mesh.mesh,
                global_actives,
                driver.inversion_mesh.mesh,
                enforce_active=False,
                components=driver.n_blocks,
            )
            tile_map = projection * wire
            driver.params.active_model = None
            driver.models.active_cells = projection.local_active
            driver.data_misfit.model_map = tile_map

            multipliers = []
            mappings = self._get_set_simulation_mappings(driver.data_misfit, tile_map)
            for mult, mapping in zip(
                driver.data_misfit.multipliers, mappings, strict=False
            ):
                multipliers.append(mult * (mapping[0].shape[0] / projection.shape[1]))

            driver.data_misfit.multipliers = multipliers
        self.validate_create_models()

    @property
    def inversion_data(self):
        """Inversion data"""
        return self._inversion_data

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None and not self.params.forward_only:
            with fetch_active_workspace(self.workspace, mode="r+"):
                directives_list = self._get_drivers_directives()

                directives_list += self._get_global_model_save_directives()
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

    @property
    def mapping(self):
        """
        Create a dictionary of mappings for all model components and drivers.

        e.g.

        mappings = {
            (driver_mvi, amplitude): P_mvi_a,
            (driver_mvi, inclination): P_mvi_i,
            ...
            (driver_fem, cond): P_fem_c,
        }

        :returns: A flat list of mappings for all drivers and all components in
            order to be used in the inversion.
        """
        if self._mapping is None:
            mappings = {}
            start = 0
            n_values = int(np.sum(self.models.active_cells))
            for driver in self.drivers:
                for mapping in driver.mapping:
                    mappings[driver, mapping] = Projection(
                        int(np.sum(self.n_values)), slice(start, start + n_values)
                    )
                    start += n_values

            self._mapping = mappings

        return self._mapping.values()

    @property
    def n_values(self):
        """Number of values in the model"""
        if self._n_values is None:
            n_values = self.models.n_active
            count = []
            for driver in self.drivers:
                n_comp = driver.n_blocks  # If vector of scalar model
                count.append(n_values * n_comp)
            self._n_values = count

        return self._n_values

    def run(self):
        """Run inversion from params"""
        if self.logger:
            sys.stdout = self.logger
            self.logger.start()
            self.configure_dask()

        if Path(self.params.input_file.path_name).is_file():
            with fetch_active_workspace(self.workspace, mode="r+"):
                self.out_group.add_file(self.params.input_file.path_name)

        if self.params.forward_only:
            print("Running the forward simulation ...")
            predicted = self.inverse_problem.get_dpred(
                self.models.starting_model, compute_J=False
            )

            for sub, driver in zip(predicted, self.drivers, strict=True):
                SaveDataGeoh5Factory(driver.params).build(
                    inversion_object=driver.inversion_data,
                ).write(0, sub)
        else:
            # Run the inversion
            self.start_inversion_message()
            self.inversion.run(self.models.starting_model)
        if self.logger:
            self.logger.end()
            sys.stdout = self.logger.terminal
            self._update_log()

    def validate_create_mesh(self):
        """Function to validate and create the inversion mesh."""

        if self.params.mesh is None:
            print("Creating a global mesh from sub-meshes parameters.")
            tree = create_octree_from_octrees(
                [driver.inversion_mesh.mesh for driver in self.drivers]
            )
            self.params.mesh = treemesh_2_octree(self.workspace, tree)

        collocate_octrees(
            self.inversion_mesh.entity,
            [driver.inversion_mesh.entity for driver in self.drivers],
        )
        for driver in self.drivers:
            driver.inversion_mesh.mesh = None

    def validate_create_models(self):
        """Create stacked model vectors from all drivers provided."""
        for model_type in self.models.model_types:
            if model_type in [
                "petrophysical_model",
                "gradient_dip",
                "gradient_direction",
                "starting_inclination",
                "starting_declination",
                "reference_inclination",
                "reference_declination",
            ]:
                continue

            model = getattr(self.models, f"_{model_type}").model

            # If set on joint driver, repeat for all drivers
            if model is not None:
                model = np.kron(np.ones(len(self.mapping)), model)

            # Concatenate models from individual drivers projected onto the global mesh
            else:
                model = []
                vec = np.zeros(self.models.n_active * len(self.mapping))
                for child_driver in self.drivers:
                    model_local_values = getattr(child_driver.models, model_type)

                    if model_local_values is None:
                        model.append(None)
                        continue

                    projection = child_driver.data_misfit.model_map.deriv(vec).T

                    if isinstance(model_local_values, float):
                        model_local_values = (
                            np.ones(projection.shape[1]) * model_local_values
                        )

                    norm = np.array(np.sum(projection, axis=1)).flatten()
                    model.append((projection * model_local_values) / (norm + 1e-8))

                # Mostly for rotated gradient mode
                is_none = [val is None for val in model]
                if any(is_none):
                    if not all(is_none):
                        logger.warning(
                            "Some drivers do not have a model of type "
                            "'%s' set. Please assign a value to individual drivers"
                            " or use the joint driver options to set it globally.\n"
                            "Parameter ignored for the inversion.",
                            model_type,
                        )
                    model = None
                else:
                    model = np.sum(model, axis=0)

            if model is not None:
                getattr(self.models, f"_{model_type}").model = model

    @property
    def wires(self):
        """
        Model projections for the simulations.

        e.g. For a joint inversion with 3 drivers, the wires will be:

        wires = [
            P_mvi(0, 3*nC),
            P_den(3*nC, 4*nC),
            P_cond(4*nC, 5*nC),
        ]

        such that the first projection grabs the first 3*nC values of the model vector.
        """
        if self._wires is None:
            collection = []
            start = 0
            for n_values in self.n_values:
                collection.append(
                    Projection(
                        int(np.sum(self.n_values)), slice(start, start + n_values)
                    )
                )
                start += n_values

            self._wires = collection

        return self._wires

    def _get_drivers_directives(self) -> list[directives.Directive]:
        """
        Create a list of directives for each driver.
        """
        self._directives = DirectivesFactory(self)
        directives_list = []
        count = 0

        if self.client:
            misfits = np.hstack(self.data_misfit._workloads).tolist()  # pylint: disable=protected-access
        else:
            misfits = self.data_misfit.objfcts

        for driver in self.drivers:
            driver_directives = DirectivesFactory(driver)

            if hasattr(driver.params.models, "model_type") and hasattr(
                self.params.models, "model_type"
            ):
                driver.params.models.model_type = self.params.models.model_type

            save_model = driver_directives.save_iteration_model_directive
            save_model.transforms = [
                driver.data_misfit.model_map,
                *save_model.transforms,
            ]

            directives_list.append(save_model)
            directives_list.append(
                SaveLPModelGroup(
                    driver.inversion_mesh.entity,
                    self._directives.update_irls_directive,
                )
            )

            if driver_directives.save_property_group is not None:
                directives_list.append(driver_directives.save_property_group)

            n_tiles = len(driver.data_misfit.objfcts)
            for name in [
                "save_iteration_data_directive",
                "save_iteration_residual_directive",
                "save_iteration_apparent_resistivity_directive",
                "vector_inversion_directive",
            ]:
                directive = getattr(driver_directives, name)
                if directive is not None:
                    directive.joint_index = [
                        misfits.index(fun) for fun in driver.data_misfit.objfcts
                    ]
                    directives_list.append(directive)

                if (
                    isinstance(directive, directives.SaveDataGeoH5)
                    and len(directive.channels) > 1
                ):
                    save_group = directives.SavePropertyGroup(
                        driver.inversion_data.entity,
                        channels=directive.channels,
                        components=directive.components,
                    )
                    directives_list.append(save_group)
            count += n_tiles

        return directives_list

    def _get_global_model_save_directives(self):
        """
        Create a list of directives for regularization models on the global mesh.
        """
        directives_list = []
        for driver, wire in zip(self.drivers, self.wires, strict=True):
            directives_list += self._get_local_model_save_directives(driver, wire)
        return directives_list

    def _get_local_model_save_directives(
        self, driver, wire
    ) -> list[directives.Directive]:
        """
        Create a save model directive on local meshes, one list per driver.
        """
        factory = SaveModelGeoh5Factory(driver.params)
        factory.factory_type = driver.params.inversion_type
        model_directive = factory.build(
            inversion_object=self.inversion_mesh,
            active_cells=self.models.active_cells,
            name="Model",
        )

        model_directive.label = driver.params.physical_property
        if getattr(driver.params.models, "model_type", None) == "Resistivity (Ohm-m)":
            model_directive.label = "resistivity_model"

        model_directive.transforms = [wire, *model_directive.transforms]

        directives_list = [model_directive]
        if driver.directives.save_property_group is not None:
            directives_list.append(
                directives.SavePropertyGroup(
                    self.inversion_mesh.entity,
                    group_type=GroupTypeEnum.DIPDIR,
                    channels=["declination", "inclination"],
                )
            )
        return directives_list

    def _overload_regularization(self, regularization: ComboObjectiveFunction):
        """
        Create a flat ComboObjectiveFunction from all drivers provided and
        add cross-gradient regularization for all combinations of model parameters.
        """
        reg_list = regularization.objfcts
        multipliers = regularization.multipliers
        reg_dict = {reg.mapping: reg for reg in reg_list}
        for driver in self.drivers:
            reg_block = []
            for mapping in driver.mapping:
                reg_block.append(reg_dict[self._mapping[driver, mapping]])

            driver.regularization = ComboObjectiveFunction(objfcts=reg_block)

        return reg_list, multipliers

    def _update_log(self):
        """Update the log with the inversion results."""
        for directive in self.directives.directive_list:
            if isinstance(directive, directives.SaveLogFilesGeoH5):
                directive.write(1)

    def _get_set_simulation_mappings(self, misfits, mapping):
        """Collect attributes from misfit objects.

        :param misfits : List of misfit objects.
        :param attribute :  Attribute to collect.

        :return: List of collected attributes.
        """
        futures = []

        for misfit in misfits.objfcts:
            if self.client:
                delayed_mapping = self.client.scatter(mapping)
                futures.append(
                    self.client.submit(
                        _get_set_mapping,
                        misfit,
                        delayed_mapping,
                        workers=self.client.who_has(misfit)[misfit.key],
                    )
                )
            else:
                futures.append(_get_set_mapping(misfit, mapping))

        if self.client:
            mappings = []
            for future in self.client.gather(futures):
                mappings.append(future)
            return mappings
        return futures


def _get_set_mapping(obj, mapping) -> list:
    """Recursively get ordering from components of misfit function."""

    mappings = []
    for fun in obj.simulation.mappings:
        mappings.append(fun * mapping)

    obj.simulation.mappings = mappings

    return mappings
