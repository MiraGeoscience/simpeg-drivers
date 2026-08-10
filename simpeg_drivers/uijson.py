# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import json
import logging
from typing import Self

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json.annotations import OptionalString
from geoh5py.ui_json.ui_json import UIJson
from packaging.version import Version
from pydantic import field_validator

from . import public_version


logger = logging.getLogger(__name__)


class SimPEGDriversUIJson(UIJson):
    """Base class for simpeg-drivers UIJson."""

    icon: str | None = None
    documentation: str | None = (
        "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html"
    )

    n_workers: int | OptionalString = None
    n_threads: int | OptionalString = None
    performance_report: bool = False
    distributed_workers: str | None = None

    _out_group_class = SimPEGGroup

    @field_validator("version", mode="before")
    @classmethod
    def verify_and_update_version(cls, value: str) -> str:
        package_version = cls.comparable_version(public_version())
        if package_version == "0.0.0":  # dynamic version did not get generated
            return value

        input_version = cls.comparable_version(value)
        if input_version != package_version:
            logger.warning(
                "Provided ui.json file version '%s' does not match the current "
                "simpeg-drivers version '%s'. This may lead to unpredictable behavior.",
                value,
                public_version(),
            )
        return value

    @staticmethod
    def comparable_version(value: str) -> str:
        """Normalize the version string for comparison.

        Remove the dev and post-release information, or the pre-release information if it is an rc version.
        Then, it will return the public version of the version object.

        Examples:
            * for version "0.2.0.post1", return "0.2.0"
            * for version "0.2.0.dev1", return "0.2.0"
            * for version "0.2.0a1.dev1", return "0.2.0a1"
            * for version "0.2.0a1", return "0.2.0a1" (unchanged)
            * for version "0.2.0rc1", return "0.2.0"
            * for version "0.2.0+local", return "0.2.0"
        """
        version = Version(value)

        # Extract the base version (major.minor.patch)
        base_version = version.base_version

        # If it's not an RC, keep any pre-release info (alpha/beta)
        if version.pre is not None and version.pre[0] != "rc":  # pylint: disable=unsubscriptable-object
            # Recreate version with pre-release but no post or local
            return f"{base_version}{version.pre[0]}{version.pre[1]}"

        # No pre-release info or it's an RC, return just the base version
        return base_version

    @classmethod
    def write_default(cls):
        """Write the default UIJson file to disk with updated version."""

        with open(cls.default_ui_json, encoding="utf-8") as file:
            data = json.load(file)
            data["version"] = public_version()

        uijson = cls.model_construct(**data)
        data = uijson.model_dump_json(indent=4, exclude_unset=False)
        with open(cls.default_ui_json, "w", encoding="utf-8") as file:
            file.write(data)

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
