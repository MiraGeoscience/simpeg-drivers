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

import importlib
import json
import re
from pathlib import Path

import pytest
import yaml
from packaging.version import Version

import simpeg_drivers


def _get_json_version() -> str:
    version_json_path = Path(__file__).resolve().parents[1] / "_version.json"
    with version_json_path.open(encoding="utf-8") as file:
        version_json = json.load(file)
    return version_json["version"]


def _get_conda_recipe_version_def() -> str:
    recipe_path = Path(__file__).resolve().parents[1] / "recipe.yaml"

    with recipe_path.open(encoding="utf-8") as file:
        recipe = yaml.safe_load(file)
    return recipe["context"]["version"]


def _version_module_exists():
    try:
        importlib.import_module("simpeg_drivers._version")
        return True
    except ModuleNotFoundError:
        return False


def test_conda_recipe_version_loads_json():
    conda_version_def = _get_conda_recipe_version_def()
    regex = (
        r"\$\{\{\s*load_from_file\(\s*['\"](_version\.json)['\"]\s*\)"
        r"\s*\.version\b.*\}\}"
    )
    regex_match = re.match(regex, conda_version_def)
    assert regex_match is not None


@pytest.mark.skipif(
    _version_module_exists(),
    reason="simpeg_drivers._version can be found: package is built",
)
def test_fallback_version_is_zero():
    project_version = Version(simpeg_drivers.__version__)
    fallback_version = Version("0.0.0.dev0")
    assert project_version.base_version == fallback_version.base_version
    assert project_version.pre is None
    assert project_version.post is None
    assert project_version.dev == fallback_version.dev


@pytest.mark.skipif(
    not _version_module_exists(),
    reason="simpeg_drivers._version cannot be found: uses a fallback version",
)
def test_version_json_is_consistent():
    project_version = Version(simpeg_drivers.__version__)
    json_version = Version(_get_json_version())
    assert project_version == json_version
