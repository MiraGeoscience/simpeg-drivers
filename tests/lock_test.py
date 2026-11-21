# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
import yaml
from packaging.utils import (
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import Version


FLOORS = {
    "certifi": "2026.10.18",
    "msgpack": "1.2.3",
    "msgpack-python": "1.2.3",
    "pillow": "13.0.0",
    "setuptools": "84.1.0",
    "tornado": "6.6.1",
    "urllib3": "2.8.0",
    "werkzeug": "3.1.9",
}
CONDA_SOURCES = {
    "bokeh",
    "defusedxml",
    "fsspec",
    "geoana",
    "pillow",
    "psutil",
    "pymatsolver",
    "zarr",
}
MIRA_SOURCES = {"geoh5py", "grid-apps", "geoapps-utils", "mira-simpeg"}


def package_info(entry):
    source, url = next(iter(entry.items()))
    filename = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
    if source == "conda":
        name, version, _ = filename.rsplit(".", 1)[0].rsplit("-", 2)
    elif filename.endswith(".whl"):
        name, version, _, _ = parse_wheel_filename(filename)
    else:
        name, version = parse_sdist_filename(filename)
    return source, canonicalize_name(name), str(version)


def check_floor(entry):
    source, name, version = package_info(entry)
    if name in FLOORS:
        assert Version(version) >= Version(FLOORS[name]), (
            source,
            name,
            version,
            FLOORS[name],
        )


def test_security_floor_checks_pypi_and_conda():
    check_floor({"pypi": "https://example.org/certifi-2026.10.18-py3-none-any.whl"})
    with pytest.raises(AssertionError):
        check_floor({"pypi": "https://example.org/certifi-2026.1.1-py3-none-any.whl"})
    with pytest.raises(AssertionError):
        check_floor({"conda": "https://example.org/pillow-12.0.0-py312_0.conda"})


def test_locked_runtime_sources_and_security_floors():
    lock = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "pixi.lock").read_text()
    )
    for environment, data in lock["environments"].items():
        if environment == "docs":
            continue
        for platform, entries in data["packages"].items():
            sources = {}
            for entry in entries:
                check_floor(entry)
                source, name, _ = package_info(entry)
                sources[name] = source
            for name in CONDA_SOURCES:
                assert sources.get(name) == "conda", (environment, platform, name)
            for name in MIRA_SOURCES:
                assert sources.get(name) == "pypi", (environment, platform, name)
