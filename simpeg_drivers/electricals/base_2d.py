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

    relief = get_max_line_relief(line_ids, drape_options.v_cell_size)

    for line_id in np.unique(line_ids.values):
        poles = get_poles_by_line_id(line_ids, line_id)
        poles = np.unique(poles, axis=0)
        poles = normalize_vertically(poles, relief)

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


def get_max_line_relief(line_ids, z_cell_size) -> float:
    """
    Get the maximum relief across all survey lines, rounded to the nearest cell thickness.

    :param line_ids: IntegerData object containing the line IDs for each vertex.
    :param z_cell_size: Cell size in the vertical direction for the drape mesh.
    """
    max_relief = 0
    for line_id in np.unique(line_ids.values):
        poles = get_poles_by_line_id(line_ids, line_id)
        max_relief = np.maximum(poles[:, 2].max() - poles[:, 2].min(), max_relief)

    return (max_relief // z_cell_size + 2) * z_cell_size


def normalize_vertically(poles: np.ndarray, relief: float) -> np.ndarray:
    """
    Given a set of pole locations, normalize the vertical component to the maximum relief across all lines.

    This ensures that the drape mesh has uniform vertical discretization across all survey lines.

    :param poles: Array of pole locations to normalize.
    :param relief: Maximum relief across all survey lines, rounded to the nearest cell thickness.

    :return: Array of pole locations with normalized vertical component.
    """
    min_poles_z = poles[:, 2].min()
    poles[:, 2] -= min_poles_z
    poles[:, 2] *= relief / poles[:, 2].max()

    # Shift back vertically
    poles[:, 2] += min_poles_z

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
