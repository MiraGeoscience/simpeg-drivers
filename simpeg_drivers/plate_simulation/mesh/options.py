# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

from geoh5py.objects import ObjectBase, Points, Surface
from octree_creation_app.params import OctreeParams
from pydantic import BaseModel


class MeshOptions(BaseModel):
    """Core parameters for octree mesh creation."""

    u_cell_size: float
    v_cell_size: float
    w_cell_size: float
    padding_distance: float
    depth_core: float
    max_distance: float
    minimum_level: int = 8
    diagonal_balance: bool = False

    def octree_params(
        self, survey: ObjectBase, topography: Surface | Points, plates: list[Surface]
    ):
        refinements = [
            {
                "refinement_object": survey,
                "levels": [4, 4, 4],
                "horizon": False,
            },
            {
                "refinement_object": topography,
                "levels": [0, 2],
                "horizon": True,
                "distance": 1000.0,
            },
        ]
        for plate in plates:
            refinements.append(
                {
                    "refinement_object": plate,
                    "levels": [2, 1],
                    "horizon": False,
                }
            )

        octree_params = OctreeParams(
            geoh5=survey.workspace,
            objects=survey,
            u_cell_size=self.u_cell_size,
            v_cell_size=self.v_cell_size,
            w_cell_size=self.w_cell_size,
            horizontal_padding=self.padding_distance,
            vertical_padding=self.padding_distance,
            depth_core=self.depth_core,
            max_distance=self.max_distance,
            minimum_level=self.minimum_level,
            diagonal_balance=self.diagonal_balance,
            refinements=refinements,
        )

        assert isinstance(survey.workspace.h5file, Path)
        path = survey.workspace.h5file.parent
        octree_params.write_ui_json(path / "octree.ui.json")
        return octree_params
