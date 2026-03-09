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

from geoh5py.ui_json.ui_json import fetch_active_workspace

from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.surveys import create_mesh_by_line_id


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
                entity = None
                if self.params.mesh is None:
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
