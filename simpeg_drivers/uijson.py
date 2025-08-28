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

import simpeg_drivers


logger = logging.getLogger(__name__)


class SimPEGDriversUIJson(BaseUIJson):
    @staticmethod
    def _version_public(value):
        # Always return only the public part of the version string
        return str(Version(str(value)).public)

    from pydantic import field_serializer

    @field_serializer("version")
    def serialize_version(self, value):
        return self._version_public(value)

    icon: str
    documentation: str = "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html"

    @field_validator("version", mode="before")
    @classmethod
    def verify_and_update_version(cls, value: str) -> str:
        if not value:
            value = simpeg_drivers.__version__
        input_version = cls.comparable_version(value)
        input_public = Version(str(value)).public
        package_public = Version(simpeg_drivers.__version__).public
        if cls.comparable_version(input_public) != cls.comparable_version(
            package_public
        ):
            logger.warning(
                "Provided ui.json file version '%s' does not match the current "
                "simpeg-drivers version '%s'. This may lead to unpredictable behavior.",
                value,
                simpeg_drivers.__version__,
            )
        return input_public

    @staticmethod
    def comparable_version(value: str) -> str:
        """Normalize the version string for comparison.

        Remove the post-release information, or the pre-release information if it is an rc version.
        For example, if the version is "0.2.0.post1", it will return "0.2.0".
        If the version is "0.2.0rc1", it will return "0.2.0".

        Then, it will return the public version of the version object.
        For example, if the version is "0.2.0+local", it will return "0.2.0".
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
        """Write the default UIJson file to disk with updated version (public only)."""

        with open(cls.default_ui_json, encoding="utf-8") as file:
            data = json.load(file)
            # Always write only the public part of the version (no local tag)
            data["version"] = str(Version(simpeg_drivers.__version__).public)

        uijson = cls.model_construct(**data)
        data = uijson.model_dump_json(indent=4, exclude_unset=False)
        with open(cls.default_ui_json, "w", encoding="utf-8") as file:
            file.write(data)
