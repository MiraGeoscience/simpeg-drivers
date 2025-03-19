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
from pydantic import field_validator

import simpeg_drivers


logger = logging.getLogger(__name__)


class SimPEGDriversUIJson(BaseUIJson):
    """Base class for simpeg-drivers UIJson."""

    icon: str
    documentation: str

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
