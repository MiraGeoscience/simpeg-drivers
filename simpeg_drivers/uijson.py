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
from pathlib import Path
from typing import Annotated

from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.shared.validators import empty_string_to_none, none_to_empty_string
from geoh5py.ui_json.enforcers import UUIDEnforcer
from geoh5py.ui_json.ui_json import BaseUIJson
from pydantic import BeforeValidator, PlainSerializer, field_validator

import simpeg_drivers


logger = logging.getLogger(__name__)


OptionalPath = Annotated[
    Path | None,
    BeforeValidator(empty_string_to_none),
    PlainSerializer(none_to_empty_string),
]


class SimPEGDriversUIJson(BaseUIJson):
    version: str = simpeg_drivers.__version__
    title: str
    icon: str
    documentation: str
    conda_environment: str
    run_command: str
    geoh5: Path | None
    monitoring_directory: OptionalPath
    workspace_geoh5: OptionalPath

    @field_validator("version", mode="before")
    @classmethod
    def verify_and_update_version(cls, value: str) -> str:
        version = simpeg_drivers.__version__
        if value != version:
            logger.warning(
                "Provided ui.json file version %s does not match the the current"
                "simpeg-drivers version %s.  This may lead to unpredictable"
                "behavior.",
                value,
                version,
            )
        return value

    @classmethod
    def write_default(cls):
        """Write the default UIJson file to disk with updated version."""

        with open(cls.default_ui_json, encoding="utf-8") as file:
            data = json.load(file)
            data["version"] = simpeg_drivers.__version__

        uijson = cls.model_construct(**data)
        data = uijson.model_dump_json(indent=4)
        with open(cls.default_ui_json, "w", encoding="utf-8") as file:
            file.write(data)
