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
from typing import ClassVar

from geoh5py import Workspace

from simpeg_drivers.uijson import CoreUIJson


logger = logging.getLogger(__name__)


def test_version_warning(tmp_path, caplog):
    workspace = Workspace(tmp_path / "test.geoh5")

    with caplog.at_level(logging.WARNING):
        _ = CoreUIJson(
            version="0.2.0",
            title="My app",
            geoh5=str(workspace.h5file),
            run_command="myapp.driver",
            monitoring_directory="",
            conda_environment="my-app",
            workspace_geoh5="",
        )


def test_write_default(tmp_path):
    default_path = tmp_path / "default.ui.json"
    data = {
        "version": "0.1.0",
        "title": "My app",
        "geoh5": "",
        "run_command": "myapp.driver",
        "monitoring_directory": "",
        "conda_environment": "my-app",
        "workspace_geoh5": "",
    }
    with open(default_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    class MyUIJson(CoreUIJson):
        default_ui_json: ClassVar[Path] = default_path
        version: str = "0.2.0"

    MyUIJson.write_default()

    with open(default_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "0.3.0-alpha.1"
