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


# pylint: disable=unexpected-keyword-arg, no-value-for-parameter

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from octree_creation_app.utils import (
    collocate_octrees,
    create_octree_from_octrees,
    treemesh_2_octree,
)
from simpeg import directives
from simpeg.maps import TileMap
from simpeg.objective_function import ComboObjectiveFunction

from simpeg_drivers import DRIVER_MAP
from simpeg_drivers.components.factories import SaveDataGeoh5Factory
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.joint.params import BaseJointParams


class BaseJointDriver(InversionDriver):
    def __init__(self, params: BaseJointParams):
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

                    for fun in driver.data_misfit.objfcts:
                        fun.name = f"Group {label.upper()} {fun.name}"

                    multipliers += [
                        getattr(self.params, f"group_{label}_multiplier") ** 2.0
                    ] * len(driver.data_misfit.objfcts)

            self._data_misfit = ComboObjectiveFunction(
                objfcts=objective_functions, multipliers=multipliers
            )

        return self._data_misfit

    @property
    def drivers(self) -> list[InversionDriver] | None:
        """List of inversion drivers."""
        if self._drivers is None:
            drivers = []
            physical_property = []
            # Create sub-drivers
            for group in self.params.groups:
                _ = group.options  # Triggers something... otherwise ui_json is empty
                group = group.copy(parent=self.params.out_group)

                ui_json = group.options
                ui_json["geoh5"] = self.workspace

                ifile = InputFile(ui_json=ui_json)
                mod_name, class_name = DRIVER_MAP.get(ui_json["inversion_type"])
                module = __import__(mod_name, fromlist=[class_name])
                inversion_driver = getattr(module, class_name)
                params = inversion_driver._params_class(  # pylint: disable=W0212
                    ifile, out_group=group
                )
                driver = inversion_driver(params)
                physical_property.append(params.physical_property)
                drivers.append(driver)

            self._drivers = drivers
            self.params.physical_property = physical_property

        return self._drivers

    def get_local_actives(self, driver: InversionDriver):
        """Get all local active cells within the global mesh for a given driver."""

        in_local = driver.inversion_mesh.mesh._get_containing_cell_indexes(  # pylint: disable=W0212
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
            projection = TileMap(
                self.inversion_mesh.mesh,
                global_actives,
                driver.inversion_mesh.mesh,
                enforce_active=False,
                components=3 if driver.inversion_data.vector else 1,
            )
            driver.params.active_model = None
            driver.models.active_cells = projection.local_active
            driver.data_misfit.model_map = projection * wire

            multipliers = []
            for mult, func in driver.data_misfit:
                func.model_map = func.model_map * driver.data_misfit.model_map
                multipliers.append(
                    mult * (func.model_map.shape[0] / projection.shape[1])
                )

            driver.data_misfit.multipliers = multipliers

        self.validate_create_models()

    @property
    def inversion_data(self):
        """Inversion data"""
        return self._inversion_data

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
        """Construct models from the local drivers."""
        raise NotImplementedError("Must be implemented by subclass.")

    @property
    def wires(self):
        """Model projections."""
        raise NotImplementedError("Must be implemented by subclass.")

    def run(self):
        """Run inversion from params"""
        sys.stdout = self.logger
        self.logger.start()
        self.configure_dask()

        if Path(self.params.input_file.path_name).is_file():
            with fetch_active_workspace(self.workspace, mode="r+"):
                self.out_group.add_file(self.params.input_file.path_name)

        if self.params.forward_only:
            print("Running the forward simulation ...")
            predicted = self.inverse_problem.get_dpred(
                self.models.starting, compute_J=False
            )

            for sub, driver in zip(predicted, self.drivers, strict=True):
                SaveDataGeoh5Factory(driver.params).build(
                    inversion_object=driver.inversion_data,
                    sorting=np.argsort(np.hstack(driver.sorting)),
                    ordering=driver.ordering,
                ).write(0, sub)
        else:
            # Run the inversion
            self.start_inversion_message()
            self.inversion.run(self.models.starting)

        self.logger.end()
        sys.stdout = self.logger.terminal
        self.logger.log.close()
        self._update_log()

    def _update_log(self):
        """Update the log with the inversion results."""
        for directive in self.directives.directive_list:
            if isinstance(directive, directives.SaveLogFilesGeoH5):
                directive.save_log()
