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

from logging import getLogger

from geoh5py.objects import DrapeModel, Octree, PotentialElectrode
from geoh5py.ui_json.ui_json import fetch_active_workspace
from pydantic import field_validator, model_validator

from simpeg_drivers.components.meshes import InversionMesh
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.options import (
    CoreOptions,
    DrapeModelOptions,
    LineSelectionOptions,
)
from simpeg_drivers.utils.surveys import create_mesh_by_line_id


logger = getLogger(__name__)


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


class DeprecatedBatch2DDriver(Base2DDriver):
    """Direct Current 2D forward driver."""

    def __init__(self, *args, **kwargs):
        logger.warning(
            "The Batch2D classes will be deprecated in version 0.5.0. "
            "Please use the non-batch classes instead. Results may be affected.",
        )

        super().__init__(*args, **kwargs)


class Base2DOptions(CoreOptions):
    """
    Base options for the Direct Current 2D forward and inverse driver.


    :param data_object: Potential electrode object.
    :param line_selection: Line selection parameters.
    :param mesh: Optional mesh object if providing a heterogeneous model.
    :param drape_model: Drape model parameters.
    """

    data_object: PotentialElectrode
    line_selection: LineSelectionOptions = LineSelectionOptions()
    mesh: DrapeModel | Octree | None = None
    drape_model: DrapeModelOptions = DrapeModelOptions()

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
