# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#
#  This file is part of simpeg-drivers.
#
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved.

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
    project_verion = Version(simpeg_drivers.__version__)
    assert conda_version.base_version == project_verion.base_version
    assert conda_version.is_prerelease == project_verion.is_prerelease
    assert conda_version.is_postrelease == project_verion.is_postrelease


def test_conda_version_is_pep440():
    version = Version(get_conda_recipe_version())
    print(version)
    assert version is not None
