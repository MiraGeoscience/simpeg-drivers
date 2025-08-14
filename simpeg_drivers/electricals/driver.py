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

import sys
import uuid
import warnings
from pathlib import Path

import numpy as np
from geoapps_utils.utils.locations import get_locations
from geoapps_utils.utils.numerical import weighted_average
from geoh5py.data import Data
from geoh5py.objects import DrapeModel
from geoh5py.ui_json.ui_json import fetch_active_workspace
from geoh5py.workspace import Workspace

from simpeg_drivers.components.data import InversionData
from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.components.topography import InversionTopography
from simpeg_drivers.components.windows import InversionWindow
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.line_sweep.driver import LineSweepDriver
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    LineSelectionOptions,
)
from simpeg_drivers.utils.surveys import extract_dcip_survey
from simpeg_drivers.utils.utils import get_drape_model


class Base2DDriver(InversionDriver):
    """Base class for 2D DC and IP forward and inversion drivers."""

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                if self.params.mesh is None:
                    self.params.mesh = self.create_drape_mesh()

                self._inversion_mesh = InversionMesh(self.workspace, self.params)
        return self._inversion_mesh

    def create_drape_mesh(self) -> DrapeModel:
        """Create a drape mesh for the inversion."""
        current_entity = self.params.data_object.current_electrodes
        receiver_locs = np.vstack(
            [self.params.data_object.vertices, current_entity.vertices]
        )
        with fetch_active_workspace(self.workspace):
            mesh = get_drape_model(
                self.workspace,
                "Models",
                receiver_locs,
                [
                    self.params.drape_model.u_cell_size,
                    self.params.drape_model.v_cell_size,
                ],
                self.params.drape_model.depth_core,
                [self.params.drape_model.horizontal_padding] * 2
                + [self.params.drape_model.vertical_padding, 1],
                self.params.drape_model.expansion_factor,
            )[0]

        return mesh


class BaseBatch2DDriver(LineSweepDriver):
    """Base class for batch 2D DC and IP forward and inversion drivers."""

    _options_class: type[BaseForwardOptions | BaseInversionOptions]
    _params_2d_class: type[BaseForwardOptions | BaseInversionOptions]
    _validations = None
    _model_list: list[str] = []

    def __init__(self, params):
        super().__init__(params)
        if params.file_control.files_only:
            sys.exit("Files written")

    def transfer_models(self, mesh: DrapeModel) -> dict[str, uuid.UUID | float]:
        """
        Transfer models from the input parameters to the output drape mesh.

        :param mesh: Destination DrapeModel object.
        """
        models = {"starting_model": self.batch2d_params.starting_model}

        for model in self._model_list:
            models[model] = getattr(self.batch2d_params, model)

        if not self.batch2d_params.forward_only:
            for model in ["reference_model", "lower_bound", "upper_bound"]:
                models[model] = getattr(self.batch2d_params, model)

        if self.batch2d_params.mesh is not None:
            xyz_in = get_locations(self.workspace, self.batch2d_params.mesh)
            xyz_out = mesh.centroids

            for name, model in models.items():
                if model is None:
                    continue
                elif isinstance(model, Data):
                    model_values = weighted_average(
                        xyz_in, xyz_out, [model.values], n=1
                    )[0]
                else:
                    model_values = model * np.ones(len(xyz_out))

                model_object = mesh.add_data({name: {"values": model_values}})
                models[name] = model_object

        return models

    def write_files(self, lookup):
        """Write ui.geoh5 and ui.json files for sweep trials."""

        kwargs_2d = {}
        with fetch_active_workspace(self.workspace, mode="r+"):
            self._window = InversionWindow(self.workspace, self.batch2d_params)
            self._inversion_data = InversionData(self.workspace, self.batch2d_params)
            self._inversion_data.save_data()
            self._inversion_topography = InversionTopography(
                self.workspace, self.batch2d_params
            )

            for uid, trial in lookup.items():
                if trial["status"] != "pending":
                    continue

                filepath = Path(self.working_directory) / f"{uid}.ui.geoh5"

                if filepath.exists():
                    warnings.warn(
                        f"File {filepath} already exists but 'status' marked as 'pending'. "
                        "Over-writing file."
                    )
                    filepath.unlink()

                with Workspace.create(filepath) as iter_workspace:
                    cell_mask: np.ndarray = (
                        self.batch2d_params.line_selection.line_object.values
                        == trial["line_id"]
                    )

                    if not np.any(cell_mask):
                        continue

                    receiver_entity = extract_dcip_survey(
                        iter_workspace, self.inversion_data.entity, cell_mask
                    )
                    current_entity = receiver_entity.current_electrodes
                    receiver_locs = np.vstack(
                        [receiver_entity.vertices, current_entity.vertices]
                    )

                    mesh = get_drape_model(
                        iter_workspace,
                        "Models",
                        receiver_locs,
                        [
                            self.batch2d_params.drape_model.u_cell_size,
                            self.batch2d_params.drape_model.v_cell_size,
                        ],
                        self.batch2d_params.drape_model.depth_core,
                        [self.batch2d_params.drape_model.horizontal_padding] * 2
                        + [self.batch2d_params.drape_model.vertical_padding, 1],
                        self.batch2d_params.drape_model.expansion_factor,
                    )[0]

                    model_parameters = self.transfer_models(mesh)

                    for key in self._params_2d_class.model_fields:
                        param = getattr(self.batch2d_params, key, None)
                        if key not in ["title", "inversion_type"]:
                            kwargs_2d[key] = param

                    self.batch2d_params.active_cells.topography_object.copy(
                        parent=iter_workspace, copy_children=True
                    )

                    kwargs_2d.update(
                        dict(
                            **{
                                "geoh5": iter_workspace,
                                "mesh": mesh,
                                "data_object": receiver_entity,
                                "line_selection": LineSelectionOptions(
                                    line_object=receiver_entity.get_data(
                                        self.batch2d_params.line_selection.line_object.name
                                    )[0],
                                    line_id=trial["line_id"],
                                ),
                                "out_group": None,
                            },
                            **model_parameters,
                        )
                    )

                params = self._params_2d_class(**kwargs_2d)
                params.write_ui_json(Path(self.working_directory) / f"{uid}.ui.json")

                lookup[uid]["status"] = "written"

        _ = self.update_lookup(lookup)  # pylint: disable=no-member
