# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from typing import Self

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json.annotations import OptionalInteger
from geoh5py.ui_json.ui_json import UIJson


class SimPEGDriversUIJson(UIJson):
    """Base class for simpeg-drivers UIJson."""

    icon: str | None = None
    documentation: str | None = (
        "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html"
    )

    n_workers: int | OptionalInteger = None
    n_threads: int | OptionalInteger = None
    performance_report: bool = False
    distributed_workers: str | None = None

    _out_group_class = SimPEGGroup

    @classmethod
    def from_dict(cls, data: dict, validate: bool = True) -> Self:
        """
        Create a UIJson instance from a dictionary.

        Deal with known issues in legacy files

        :param data: Dictionary representing the ui json object.
        :param validate: Whether to validate the data against the model schema.

        :returns: UIJson object.
        """
        kwargs = {}
        for key, item in data.items():
            # Tile spatial not a Data selector
            if isinstance(item, dict) and key == "tile_spatial":
                item.pop("isValue", None)
                item.pop("property", None)
                item.pop("parent", None)
                item.pop("association", None)

            # Old default not in choiceList
            if key == "data_units" and item["value"] not in item["choiceList"]:
                item["value"] = item["choiceList"][0]

            # Ignore active model if topography object is non-optional
            if key == "active_model":
                topo_form = data["topography_object"]
                if not topo_form["optional"]:
                    continue

            kwargs[key] = item if item != "" else None

        if "geoh5" not in kwargs:
            kwargs["geoh5"] = ""

        ui_json_class = cls.infer(**kwargs)

        if validate:
            return ui_json_class(**kwargs)

        return ui_json_class.model_construct(**kwargs)  # type: ignore[return-value, arg-type]
