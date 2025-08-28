# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import json
import logging

from geoh5py.ui_json.ui_json import BaseUIJson
from packaging.version import Version
from pydantic import field_validator

from . import public_version


logger = logging.getLogger(__name__)


class SimPEGDriversUIJson(BaseUIJson):
    """Base class for simpeg-drivers UIJson."""

    icon: str
    documentation: str = "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html"

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
