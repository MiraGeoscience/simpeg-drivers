# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=unexpected-keyword-arg, no-value-for-parameter

from __future__ import annotations

from logging import getLogger
from typing import Any

import numpy as np
import simpeg.dask.objective_function as dask_objective_function
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import DrapeModel, Octree
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
    SaveModelGeoh5Factory,
)
from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import InversionDriver, first_child_of_type
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.options import ModelTypeEnum
from simpeg_drivers.utils.utils import simpeg_group_to_driver


logger = getLogger(__name__)


class BaseJointDriver(InversionDriver):
    def __init__(self, params: BaseJointOptions):
        self._directives = None
        self._drivers = None
        self._wires = None
        self._is_initialized = False

        super().__init__(params)

    @property
    def data_misfit(self):
        if getattr(self, "_data_misfit", None) is None and self.drivers is not None:
            objective_functions = []
            multipliers = []
            tiles = []
            for label, driver in zip("abc", self.drivers, strict=False):
                if driver.data_misfit is not None:
                    objective_functions += driver.data_misfit.objfcts

                    for ii, fun in enumerate(driver.data_misfit.objfcts):
                        fun.name = f"Group_{label.upper()}:Tile_{ii}"

                    multipliers += (
                        [
                            (getattr(self.params, f"group_{label}_multiplier") or 1.0)
                            ** 2.0
                            * driver.directives.update_irls_directive.chifact_target  # Adjust for local chi factors
                        ]
                        * len(driver.data_misfit.objfcts)
                    )
                    tiles.append(driver.tiles)

            self.tiles = tiles
            if self.client:
                combo = dask_objective_function.DistributedComboMisfits(
                    objfcts=objective_functions,
                    multipliers=multipliers,
                    client=self.client,
                )
                return combo

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

    def get_nested_tiles(self):
        """Get nested tiles from all drivers."""
        all_tiles = []
        for driver in self.drivers:
            if self.params.directives.auto_scale_misfits:
                all_tiles.append(driver.get_nested_tiles())
            else:
                all_tiles += driver.get_nested_tiles()

        return all_tiles

    def initialize(self):
        """Generate sub drivers."""

        if self._is_initialized:
            return

        self.validate_create_mesh()

        # Add re-projection to the global mesh
        global_actives = np.zeros(self.inversion_mesh.mesh.nC, dtype=bool)
        for driver in self.drivers:
            local_actives = self.get_local_actives(driver)
            global_actives |= local_actives

        self.models.active_cells = global_actives

        # Set the model as input to the sub-drivers to force interpolation
        # onto their respective mesh
        for name, val in self.params.models.model_dump().items():
            if not val:
                continue

            if not hasattr(self.drivers[0].params.models, name):
                continue

            for child_driver in self.drivers:
                setattr(child_driver.params.models, name, val)

        for driver, wire in zip(self.drivers, self.wires, strict=True):
            logger.info("Initializing driver %s", driver.params.name)
            # Create a projection from global mesh to driver specific mesh
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

            # Keep a copy on the top combo/future for saving directives and model creation
            driver.data_misfit.model_map = tile_map

            multipliers = []
            mappings = self._get_set_simulation_mappings(driver.data_misfit, tile_map)
            for mult, shape in zip(
                driver.data_misfit.multipliers, mappings, strict=False
            ):
                multipliers.append(mult * (shape / projection.shape[1]))

            driver.data_misfit.multipliers = multipliers

        self.validate_create_models()

        self._is_initialized = True

    @property
    def inversion_data(self):
        """Inversion data"""
        return self._inversion_data

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None and not self.params.forward_only:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._directives.directive_list = self._get_joint_directives()

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

    def simpeg_run(self):
        """Run inversion from params"""
        self.initialize()
        self.inversion.run(self.models.starting_model)

    def validate_create_mesh(self):
        """Function to validate and create the inversion mesh."""

        if self.params.mesh is None:
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
                "starting_inclination",
                "starting_declination",
                "reference_inclination",
                "reference_declination",
            ]:
                continue

            model_collection = getattr(self.models, f"_{model_type}")

            # If set on joint driver, repeat for all drivers
            if (
                model_collection.model is not None
                and model_collection.trim_active_cells
            ):
                model = np.tile(model_collection.model, len(self.mapping))

            # Concatenate models from individual drivers projected onto the global mesh
            else:
                model = []
                vec = np.zeros(self.models.n_active * len(self.mapping))
                for child_driver in self.drivers:
                    model_local_values = getattr(child_driver.models, model_type)

                    if model_local_values is None:
                        model.append(None)
                        continue

                    if model_collection.trim_active_cells:
                        projection = child_driver.data_misfit.model_map.deriv(vec).T

                        if isinstance(model_local_values, float):
                            model_local_values = (
                                np.ones(projection.shape[1]) * model_local_values
                            )

                        norm = np.array(np.sum(projection, axis=1)).flatten()
                        model.append((projection * model_local_values) / (norm + 1e-8))
                    else:
                        ind = child_driver.inversion_mesh.mesh.get_containing_cells(
                            self.inversion_mesh.mesh.cell_centers
                        )
                        model.append(model_local_values[ind] / len(self.drivers))

                model = self._validate_model_consistency(model, model_type)
                if model:
                    model = np.sum(model, axis=0)

            if model is not None:
                getattr(self.models, f"_{model_type}").model = model

    def _reset_models(self, iteration: int):
        """
        Reset the inversion models based on specified iteration and mesh.

        :param iteration: The iteration number to reset the models for.
        """
        drivers = []
        # Create sub-drivers
        for group in self.out_group.children:
            if not isinstance(group, SimPEGGroup):
                continue

            driver = simpeg_group_to_driver(group, self.workspace)
            driver._reset_models(iteration)  # pylint: disable=protected-access
            drivers.append(driver)

        self._drivers = drivers

    def _reset_on_iteration(self, start_iteration: int):
        """
        Reset the inversion parameters to a given iteration and beta value.

        Assumes that the workspace is already opened to access data.

        :param start_iteration: Iteration number to start back at.
        """

        self._reset_models(start_iteration)

        mesh = first_child_of_type(self.out_group, (DrapeModel, Octree))
        self._inversion_mesh = InversionMesh(self.workspace, self.params, entity=mesh)

        self.initialize()

        self.optimization.iter = start_iteration
        self._reset_directives(start_iteration)

    @staticmethod
    def _validate_model_consistency(model: list[None | Any], model_type: str):
        """
        Check consistency of model values across drivers for a given model type.
        If some drivers have None and others have values, log a warning and ignore the model for the inversion.
        """
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

        return model

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
            driver_directives = driver.directives

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
                    self.workspace.get_entity(save_model.h5_object)[0],
                    self._directives.update_irls_directive,
                )
            )

            if driver_directives.save_model_groups is not None:
                directives_list.append(driver_directives.save_model_groups)

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

    def _get_joint_directives(self) -> list[directives.Directive]:
        """
        Create a list of directives for the joint inversion.
        """
        directives_list = self._get_drivers_directives()
        directives_list += self._get_global_model_save_directives()
        directives_list.append(
            directives.SaveLPModelGroup(
                self.inversion_mesh.entity,
                self._directives.update_irls_directive,
            )
        )
        directives_list.append(self._directives.save_iteration_log_files)
        directives_list += self._directives.inversion_directives
        DirectivesFactory.configure_save_directives(directives_list)
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

        if (
            getattr(driver.params.models, "model_type", None)
            == ModelTypeEnum.resistivity
        ):
            model_directive.label = "resistivity_model"
            group_name = ["resistivity"]
        elif "magnetic vector" in driver.params.inversion_type:
            group_name = ["amplitude", "inclination", "declination"]
        else:
            group_name = [driver.params.physical_property]

        model_directive.transforms = [wire, *model_directive.transforms]
        group_directive = directives.SaveModelGroup(
            self.inversion_mesh.entity,
            components=group_name,
        )

        return [model_directive, group_directive]

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
        if self.client:
            mapping = self.client.scatter(mapping)

        for misfit in misfits.objfcts:
            if self.client:
                futures.append(
                    self.client.submit(
                        _get_set_mapping,
                        misfit,
                        mapping,
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

    return mappings[0].shape[0]
