# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import numpy as np
from geoapps_utils.utils.locations import get_locations
from geoapps_utils.utils.numerical import weighted_average
from geoh5py.data import Data, IntegerData
from geoh5py.groups import PropertyGroup
from geoh5py.objects import DrapeModel, PotentialElectrode
from geoh5py.shared.merging.drape_model import DrapeModelMerger
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
    DrapeModelOptions,
    LineSelectionOptions,
)
from simpeg_drivers.utils.surveys import extract_dcip_survey
from simpeg_drivers.utils.utils import get_drape_model


class Base2DDriver(InversionDriver):
    """
    Base class for 2D DC and IP forward and inversion drivers.

    Survey lines are inverted independently and internally stacked as a single
    long survey. The inversion mesh is created as a drape mesh over the survey lines.
    """

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                entity = self.params.mesh
                if entity is None:
                    entity = create_mesh_by_line_id(
                        self.workspace,
                        self.params.line_selection.line_object,
                        self.params.drape_model,
                        parent=self.out_group,
                    )

                self._inversion_mesh = InversionMesh(
                    self.workspace, self.params, entity=entity
                )

        return self._inversion_mesh


def create_mesh_by_line_id(
    workspace: Workspace,
    line_ids: IntegerData,
    drape_options: DrapeModelOptions,
    **object_kwargs,
) -> DrapeModel:
    """
    Create a drape mesh for the dc resistivity survey lines.

    :param workspace: Workspace to create the drape mesh in.
    :param line_ids: IntegerData object containing the line IDs for each vertex.
    :param drape_options: DrapeModelOptions containing the parameters for the drape mesh
    :param object_kwargs: Additional keyword arguments to pass to the DrapeModelMerger.create_object method.

    :return: A DrapeModel object containing the merged drape mesh for all survey lines.
    """
    drape_models = []
    temp_work = Workspace()
    for line_id in np.unique(line_ids.values):
        poles = get_poles_by_line_id(line_ids, line_id)
        poles = np.unique(poles, axis=0)
        poles = normalize_vertically(poles, line_ids.parent, drape_options.v_cell_size)

        drape_model = get_drape_model(
            temp_work,
            poles,
            [
                drape_options.u_cell_size,
                drape_options.v_cell_size,
            ],
            drape_options.depth_core,
            [drape_options.horizontal_padding] * 2
            + [drape_options.vertical_padding, 1],
            drape_options.expansion_factor,
        )
        drape_models.append(drape_model)

    entity = DrapeModelMerger.create_object(workspace, drape_models, **object_kwargs)

    return entity


def normalize_vertically(
    poles: np.ndarray, survey: PotentialElectrode, z_cell_size
) -> np.ndarray:
    """
    Given a set of pole locations, normalize the vertical component to the minimum
    and maximum elevations of the survey electrodes, rounded to the nearest cell thickness.

    This ensures that the drape mesh has uniform vertical discretization across all survey lines.

    :param poles: Array of pole locations to normalize.
    :param survey: PotentialElectrode object containing the survey electrode locations.
    :param z_cell_size: Cell size in the vertical direction for rounding the minimum and maximum

    :return: Array of pole locations with normalized vertical component.
    """
    min_elev = np.min(np.r_[survey.vertices[:, 2], survey.complement.vertices[:, 2]])
    max_elev = np.max(np.r_[survey.vertices[:, 2], survey.complement.vertices[:, 2]])

    delta = ((max_elev - min_elev) // z_cell_size + 2) * z_cell_size
    min_poles_z = poles[:, 2].min()
    poles[:, 2] -= min_poles_z
    poles[:, 2] *= delta / poles[:, 2].max()

    # Shift back vertically and round to the nearest cell size to align
    poles[:, 2] += (min_poles_z // z_cell_size - 1) * z_cell_size

    return poles


def get_poles_by_line_id(line_ids: IntegerData, uid: int) -> np.ndarray:
    """Get the vertices associated with a given line ID."""
    mn_mask = line_ids.values == uid

    unique_tx = np.unique(line_ids.parent.ab_cell_id.values[mn_mask])

    ab_mask = np.isin(line_ids.parent.complement.ab_cell_id.values, unique_tx)

    return np.vstack(
        [
            line_ids.parent.vertices[line_ids.parent.cells[mn_mask].flatten()],
            line_ids.parent.current_electrodes.vertices[
                line_ids.parent.current_electrodes.cells[ab_mask].flatten()
            ],
        ]
    )


# class BaseBatch2DDriver(LineSweepDriver):
#     """Base class for batch 2D DC and IP forward and inversion drivers."""
#
#     _params_class: type[BaseForwardOptions | BaseInversionOptions]
#     _params_2d_class: type[BaseForwardOptions | BaseInversionOptions]
#
#     _model_list: list[str] = []
#
#     def __init__(self, params):
#         super().__init__(params)
#         if params.file_control.files_only:
#             sys.exit("Files written")
#
#     def transfer_models(self, mesh: DrapeModel) -> dict[str, uuid.UUID | float]:
#         """
#         Transfer models from the input parameters to the output drape mesh.
#
#         :param mesh: Destination DrapeModel object.
#         """
#         models = {"starting_model": self.batch2d_params.models.starting_model}
#
#         for model in self._model_list:
#             models[model] = getattr(self.batch2d_params, model, None)
#
#         if not self.batch2d_params.forward_only:
#             for model in ["reference_model", "lower_bound", "upper_bound"]:
#                 models[model] = getattr(self.batch2d_params.models, model)
#
#             if self.batch2d_params.models.gradient_rotation is not None:
#                 group_properties = {}
#                 for prop in self.batch2d_params.models.gradient_rotation.properties:
#                     model = self.batch2d_params.mesh.get_data(prop)[0]
#                     group_properties[model.name] = model
#
#                 models.update(group_properties)
#
#         if self.batch2d_params.mesh is not None:
#             xyz_in = get_locations(self.workspace, self.batch2d_params.mesh)
#             xyz_out = mesh.centroids
#
#             for name, model in models.items():
#                 if model is None:
#                     continue
#                 elif isinstance(model, Data):
#                     model_values = weighted_average(
#                         xyz_in, xyz_out, [model.values], n=1
#                     )[0]
#                 else:
#                     model_values = model * np.ones(len(xyz_out))
#
#                 model_object = mesh.add_data({name: {"values": model_values}})
#                 models[name] = model_object
#
#             if (
#                 not self.batch2d_params.forward_only
#                 and self.batch2d_params.models.gradient_rotation is not None
#             ):
#                 pg = PropertyGroup(
#                     mesh,
#                     properties=[models[prop] for prop in group_properties],
#                     property_group_type=self.batch2d_params.models.gradient_rotation.property_group_type,
#                 )
#                 models["gradient_rotation"] = pg
#                 del models["azimuth"]
#                 del models["dip"]
#
#         return models
#
#     def write_files(self, lookup):
#         """Write ui.geoh5 and ui.json files for sweep trials."""
#
#         kwargs_2d = {}
#         with fetch_active_workspace(self.workspace, mode="r+"):
#             for uid, trial in lookup.items():
#                 if trial["status"] != "pending":
#                     continue
#
#                 filepath = Path(self.working_directory) / f"{uid}.ui.geoh5"
#
#                 if filepath.exists():
#                     warnings.warn(
#                         f"File {filepath} already exists but 'status' marked as 'pending'. "
#                         "Over-writing file."
#                     )
#                     filepath.unlink()
#
#                 with Workspace.create(filepath) as iter_workspace:
#                     cell_mask: np.ndarray = (
#                         self.batch2d_params.line_selection.line_object.values
#                         == trial["line_id"]
#                     )
#
#                     if not np.any(cell_mask):
#                         continue
#
#                     receiver_entity = extract_dcip_survey(
#                         iter_workspace, self.inversion_data.entity, cell_mask
#                     )
#                     current_entity = receiver_entity.current_electrodes
#                     receiver_locs = np.vstack(
#                         [receiver_entity.vertices, current_entity.vertices]
#                     )
#
#                     mesh = get_drape_model(
#                         iter_workspace,
#                         "Models",
#                         receiver_locs,
#                         [
#                             self.batch2d_params.drape_model.u_cell_size,
#                             self.batch2d_params.drape_model.v_cell_size,
#                         ],
#                         self.batch2d_params.drape_model.depth_core,
#                         [self.batch2d_params.drape_model.horizontal_padding] * 2
#                         + [self.batch2d_params.drape_model.vertical_padding, 1],
#                         self.batch2d_params.drape_model.expansion_factor,
#                     )[0]
#
#                     model_parameters = self.transfer_models(mesh)
#
#                     for key in self._params_2d_class.model_fields:
#                         param = getattr(self.batch2d_params, key, None)
#                         if key not in ["title", "inversion_type"]:
#                             kwargs_2d[key] = param
#
#                     self.batch2d_params.active_cells.topography_object.copy(
#                         parent=iter_workspace, copy_children=True
#                     )
#
#                     kwargs_2d.update(
#                         dict(
#                             **{
#                                 "geoh5": iter_workspace,
#                                 "mesh": mesh,
#                                 "data_object": receiver_entity,
#                                 "line_selection": LineSelectionOptions(
#                                     line_object=receiver_entity.get_data(
#                                         self.batch2d_params.line_selection.line_object.name
#                                     )[0],
#                                     line_id=trial["line_id"],
#                                 ),
#                                 "out_group": None,
#                             },
#                             **model_parameters,
#                         )
#                     )
#
#                 params = self._params_2d_class(**kwargs_2d)
#                 params.write_ui_json(Path(self.working_directory) / f"{uid}.ui.json")
#
#                 lookup[uid]["status"] = "written"
#
#         _ = self.update_lookup(lookup)  # pylint: disable=no-member
#
#     @property
#     def inversion_data(self) -> InversionData:
#         """Inversion data"""
#         if getattr(self, "_inversion_data", None) is None:
#             with fetch_active_workspace(self.workspace, mode="r+"):
#                 self._inversion_data = InversionData(
#                     self.workspace, self.batch2d_params
#                 )
#
#         return self._inversion_data
#
#     @property
#     def inversion_topography(self):
#         """Inversion topography"""
#         if getattr(self, "_inversion_topography", None) is None:
#             self._inversion_topography = InversionTopography(
#                 self.workspace, self.batch2d_params
#             )
#         return self._inversion_topography
