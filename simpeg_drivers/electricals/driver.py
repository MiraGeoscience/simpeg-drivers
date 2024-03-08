#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

import sys
import uuid
from copy import deepcopy
from pathlib import Path

import numpy as np
from geoapps_utils.locations import get_locations
from geoapps_utils.numerical import weighted_average
from geoh5py.data import Data
from geoh5py.objects import DrapeModel
from geoh5py.workspace import Workspace

from simpeg_drivers.components.data import InversionData
from simpeg_drivers.components.topography import InversionTopography
from simpeg_drivers.components.windows import InversionWindow
from simpeg_drivers.line_sweep.driver import LineSweepDriver
from simpeg_drivers.params import BaseParams
from simpeg_drivers.utils.surveys import extract_dcip_survey
from simpeg_drivers.utils.utils import get_drape_model


class BasePseudo3DDriver(LineSweepDriver):
    _params_class: type(BaseParams)
    _params_2d_class: type(BaseParams)
    _validations: dict
    _model_list: list[str] = []

    def __init__(self, params):  # pylint: disable=useless_super_delegation
        super().__init__(params)
        if params.files_only:
            sys.exit("Files written")

    def transfer_models(self, mesh: DrapeModel) -> dict[str, uuid.UUID | float]:
        """
        Transfer models from the input parameters to the output drape mesh.

        :param mesh: Destination DrapeModel object.
        """
        models = {"starting_model": self.pseudo3d_params.starting_model}

        for model in self._model_list:
            models[model] = getattr(self.pseudo3d_params, model)

        if not self.pseudo3d_params.forward_only:
            for model in ["reference_model", "lower_bound", "upper_bound"]:
                models[model] = getattr(self.pseudo3d_params, model)

        if self.pseudo3d_params.mesh is not None:
            xyz_in = get_locations(self.workspace, self.pseudo3d_params.mesh)
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
                models[name] = model_object.uid

        return models

    def write_files(self, lookup):
        """Write ui.geoh5 and ui.json files for sweep trials."""

        forward_only = self.pseudo3d_params.forward_only
        ifile = self._params_2d_class(forward_only=forward_only).input_file

        with self.workspace.open(mode="r+"):
            self._window = InversionWindow(self.workspace, self.pseudo3d_params)
            self._inversion_data = InversionData(self.workspace, self.pseudo3d_params)
            self._inversion_topography = InversionTopography(
                self.workspace, self.pseudo3d_params
            )

            for uid, trial in lookup.items():
                if trial["status"] != "pending":
                    continue

                filepath = Path(self.working_directory) / f"{uid}.ui.geoh5"
                with Workspace(filepath) as iter_workspace:
                    cell_mask: np.ndarray = (
                        self.pseudo3d_params.line_object.values == trial["line_id"]
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
                            self.pseudo3d_params.u_cell_size,
                            self.pseudo3d_params.v_cell_size,
                        ],
                        self.pseudo3d_params.depth_core,
                        [self.pseudo3d_params.horizontal_padding] * 2
                        + [self.pseudo3d_params.vertical_padding, 1],
                        self.pseudo3d_params.expansion_factor,
                    )[0]

                    model_parameters = self.transfer_models(mesh)

                    for key in ifile.data:
                        param = getattr(self.pseudo3d_params, key, None)
                        if key not in ["title", "inversion_type"]:
                            ifile.data[key] = param

                    self.pseudo3d_params.topography_object.copy(
                        parent=iter_workspace, copy_children=True
                    )

                    ifile.data.update(
                        dict(
                            **{
                                "geoh5": iter_workspace,
                                "mesh": mesh,
                                "data_object": receiver_entity,
                                "line_id": trial["line_id"],
                                "out_group": None,
                            },
                            **model_parameters,
                        )
                    )

                ifile.name = f"{uid}.ui.json"
                ifile.path = self.working_directory  # pylint: disable=no-member
                ifile.write_ui_json()
                lookup[uid]["status"] = "written"

        _ = self.update_lookup(lookup)  # pylint: disable=no-member
