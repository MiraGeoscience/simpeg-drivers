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

from abc import ABC
from logging import getLogger
from typing import Any

import numpy as np
from geoh5py.data import FloatData, IntegerData
from geoh5py.objects import DrapeModel, Octree, PotentialElectrode
from geoh5py.ui_json.ui_json import fetch_active_workspace
from pydantic import AliasChoices, Field, field_validator, model_validator
from simpeg import optimization

from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import BaseDriver
from simpeg_drivers.options import (
    CoreOptions,
    DrapeModelOptions,
    LineSelectionOptions,
    ModelOptions,
    ModelTypeEnum,
)
from simpeg_drivers.utils.surveys import (
    create_mesh_by_line_id,
    get_parts_from_electrodes,
)


logger = getLogger(__name__)


class Conductivity2DModelOptions(ModelOptions):
    """
    Options for the conductivity model of 2D inverse problems.

    :param conductivity_model: Conductivity model or background conductivity value.
    :param model_type: Either a 'conductivity' or 'resistivity' model. The default is 'conductivity'.
    :param length_scale_y: Overloads length scales in y direction since not used in 2D inversions.
    :param y_norm: Overloads norm in the y direction since not used in 2D inversions.
    """

    model_type: ModelTypeEnum = ModelTypeEnum.conductivity
    conductivity_model: float | FloatData | IntegerData | None = Field(
        None,
        validation_alias=AliasChoices("background_conductivity", "conductivity_model"),
    )

    length_scale_y: None = None
    y_norm: None = None


class Base2DOptions(CoreOptions):
    """
    Base options for the Direct Current 2D forward and inverse driver.


    :param data_object: Potential electrode object.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters.
    """

    data_object: PotentialElectrode
    line_selection: LineSelectionOptions | None = None
    mesh: DrapeModel | Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()

    _line_parts: np.ndarray | None = None
    _selected_parts: list[int] | None = None

    @field_validator("mesh", mode="before")
    @classmethod
    def mesh_cannot_be_octree(cls, value: Octree | DrapeModel):
        if isinstance(value, Octree):
            logger.warning(
                "DC 2D forward and inversion no longer support Octree meshes as input. "
                "The program will attempt to transfer models onto the newly created DrapeModel. "
                "Results may be affected."
            )
            return None
        return value

    @model_validator(mode="before")
    @classmethod
    def deprecated_pseudo(cls, data: dict):
        if "pseudo 3d" in data.get("inversion_type", ""):
            logger.warning(
                "The Batch2D classes will be deprecated in version 0.5.0. "
                "Please use the non-batch classes instead. Results may be affected.",
            )
            data["inversion_type"] = data["inversion_type"].replace("pseudo 3d", "2d")
            line_selection = data.get("line_selection", None)
            if line_selection is None:
                line_selection = LineSelectionOptions().model_dump()

            line_selection["line_id"] = None
            data["line_selection"] = line_selection

        return data

    @property
    def line_parts(self) -> np.ndarray:
        """
        Generate monotonic line parts from line identifier or inferred from graph of potentials.
        """
        if self._line_parts is None:
            if (
                self.line_selection is not None
                and self.line_selection.property is not None
            ):
                _, self._line_parts = np.unique(
                    self.line_selection.property.values, return_inverse=True
                )
            else:
                self._line_parts = get_parts_from_electrodes(self.data_object)

        return self._line_parts

    @property
    def selected_parts(self) -> list[int]:
        """
        Translate line section ids to monotonic parts.
        """
        if self._selected_parts is None:
            parts = []
            if (
                self.line_selection is not None
                and self.line_selection.property is not None
                and self.line_selection.value is not None
            ):
                for count, val in enumerate(
                    np.unique(self.line_selection.property.values)
                ):
                    if val in self.line_selection.value:
                        parts.append(count)
            else:
                parts = np.arange(len(np.unique(self.line_parts))).tolist()

            self._selected_parts = parts

        return self._selected_parts


class Base2DDriver(BaseDriver, ABC):
    """
    Base class for 2D DC and IP forward and inversion drivers.

    Survey lines are inverted independently and internally stacked as a single
    long survey. The inversion mesh is created as a drape mesh over the survey lines.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._optimization: optimization.ProjectedGNCG | None = None

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                entity = None
                if self.params.mesh is None:
                    entity = create_mesh_by_line_id(
                        self.workspace,
                        self.params.data_object,
                        self.params.line_parts,
                        self.params.drape_model,
                        parent=self.out_group,
                    )
                    self.params.mesh = entity

                self._inversion_mesh = InversionMesh(
                    self.workspace, self.params, entity=entity
                )

        return self._inversion_mesh

    @property
    def optimization(self) -> optimization.ProjectedGNCG:
        """
        Over-loaded optimization object with bounds and active set scaling.

        Edge cells of each survey line are set to be static in the inversion.
        This is done to mitigate edge effects in the inversion results.
        """
        if getattr(self, "_optimization", None) is None:
            if self.params.forward_only:
                return optimization.ProjectedGNCG(cg_rtol=1.0)

            edge_cells = self._get_edge_cells()
            lower_bound = self.models.lower_bound
            lower_bound[edge_cells] = self.models.starting_model[edge_cells]
            upper_bound = self.models.upper_bound
            upper_bound[edge_cells] = self.models.starting_model[edge_cells]
            self._optimization = optimization.ProjectedGNCG(
                maxIter=self.params.optimization.max_global_iterations,
                lower=lower_bound,
                upper=upper_bound,
                maxIterLS=self.params.optimization.max_line_search_iterations,
                cg_maxiter=self.params.optimization.max_cg_iterations,
                cg_rtol=self.params.optimization.tol_cg,
                active_set_grad_scale=~edge_cells * 1e-8,
                LSshorten=0.25,
                require_decrease=False,
            )
        return self._optimization

    def get_tiles(self) -> dict[None, list[list[np.ndarray[tuple[Any, ...]]]]]:
        """
        Generate tiles from survey parts.
        """
        tiles = [
            [np.where(self.params.line_parts == part)[0]]
            for part in self.params.selected_parts
        ]
        if self.workers is not None and len(self.workers) > len(tiles):
            self._workers = self.workers[: len(tiles)]

        return {None: tiles}

    def _get_edge_cells(self) -> np.ndarray:
        """
        Create a boolean array of edge cells in the inversion mesh. Edge cells are defined as
        the first and last column of cell of each survey line, as well as the bottom row of cells.
        """

        edge_cells = np.zeros(self.inversion_mesh.entity.n_cells, dtype=bool)
        count = 0
        for ind in range(len(self.inversion_mesh.entity.prisms)):
            n_layers = int(self.inversion_mesh.entity.prisms[ind, -1])

            if (
                ind == 0
                or ind == len(self.inversion_mesh.entity.prisms) - 1
                or self.inversion_mesh.entity.prisms[ind + 1, -1] == 1
                or self.inversion_mesh.entity.prisms[ind - 1, -1] == 1
            ):
                edge_cells[count : count + n_layers] = True

            # Make bottom row also static
            edge_cells[count + n_layers - 1] = True
            count += n_layers

        return (self.inversion_mesh.permutation @ edge_cells)[
            self.models.active_cells
        ].astype(bool)
