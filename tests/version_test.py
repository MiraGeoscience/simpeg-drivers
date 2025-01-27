# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from pathlib import Path

import tomli as toml
import yaml
from jinja2 import Template
from packaging.version import Version

import simpeg_drivers


def get_conda_recipe_version():
    path = Path(__file__).resolve().parents[1] / "meta.yaml"

    with open(str(path), encoding="utf-8") as file:
        content = file.read()

    template = Template(content)
    rendered_yaml = template.render()

    recipe = yaml.safe_load(rendered_yaml)

    return recipe["package"]["version"]


def test_version_is_consistent():
    conda_version = Version(get_conda_recipe_version())
    project_version = Version(simpeg_drivers.__version__)
    assert conda_version.base_version == project_version.base_version
    assert conda_version.is_prerelease == project_version.is_prerelease
    assert conda_version.is_postrelease == project_version.is_postrelease


def test_conda_version_is_pep440():
    version = Version(get_conda_recipe_version())
    assert version is not None
