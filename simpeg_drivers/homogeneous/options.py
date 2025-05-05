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
from typing import ClassVar

from geoapps_utils.driver.data import BaseData
from geoh5py.data import ReferencedData
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.objects import Octree
from geoh5py.ui_json.utils import fetch_active_workspace
from pydantic import ConfigDict, model_validator

from simpeg_drivers import __version__, assets_path
from simpeg_drivers.options import CoreOptions


class HomogeneousOptions(BaseData):
    """
    Parameters for the tile estimator.
    """

    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,
        extra="allow",
        validate_default=True,
    )

    icon: str | None = None
    documentation: str | None = None
    version: str = __version__
    run_command: str = "simpeg_drivers.driver"
    conda_environment: str = "simpeg_drivers"

    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/homogeneous_inversion.ui.json"
    )

    name: ClassVar[str] = "Homogeneous Inversion"

    title: str = "Homogeneous Inversion"
    physical_property: str = "SI"
    inversion_type: str = "homogeneous"

    inversion_group: SimPEGGroup
    mesh: Octree
    geo_model: ReferencedData
    out_group: SimPEGGroup | None = None

    @model_validator(mode="before")
    @classmethod
    def out_group_if_none(cls, data):
        group = data.get("out_group", None)

        if isinstance(group, SimPEGGroup):
            return data

        if isinstance(group, UIJsonGroup | type(None)):
            name = (
                cls.model_fields["title"].default  # pylint: disable=unsubscriptable-object
                if group is None
                else group.name
            )
            with fetch_active_workspace(data["geoh5"], mode="r+") as geoh5:
                group = SimPEGGroup.create(geoh5, name=name)

        data["out_group"] = group

        return data

    @model_validator(mode="after")
    def update_out_group_options(self):
        assert self.out_group is not None
        with fetch_active_workspace(self.geoh5, mode="r+"):
            self.out_group.options = self.serialize()
            self.out_group.metadata = None
        return self
