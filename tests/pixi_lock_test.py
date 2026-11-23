# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import tomllib
from pathlib import Path

import yaml
from packaging.utils import canonicalize_name


def locked_pypi_names(entries, packages):
    return {
        canonicalize_name(packages[entry["pypi"]])
        for entry in entries
        if "pypi" in entry
    }


def test_locked_pypi_names_with_git_source():
    url = "git+https://github.com/MiraGeoscience/geoh5py.git@release/ga-4.9"
    assert locked_pypi_names([{"pypi": url}], {url: "geoh5py"}) == {"geoh5py"}


def test_locked_pypi_sources():
    """Test that the only packages resolved from PyPI are the ones specified in the mira-pypi feature."""

    package_root = Path(__file__).resolve().parents[1]
    pixi = tomllib.loads((package_root / "pixi.toml").read_text())
    mira_sources = {
        canonicalize_name(name)
        for name in pixi["feature"]["mira-pypi"]["pypi-dependencies"]
    }
    lock = yaml.safe_load((package_root / "pixi.lock").read_text())
    packages = {
        package["pypi"]: package["name"]
        for package in lock["packages"]
        if "pypi" in package
    }
    for environment, data in lock["environments"].items():
        if environment == "docs":
            continue
        for platform, entries in data["packages"].items():
            pypi_sources = locked_pypi_names(entries, packages)
            assert pypi_sources == mira_sources, (
                environment,
                platform,
                mira_sources - pypi_sources,
                pypi_sources - mira_sources,
            )
