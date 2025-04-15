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

import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.ui_json.annotations import Deprecated
from packaging.version import Version
from pydantic import AliasChoices, Field

import simpeg_drivers
from simpeg_drivers.options import ActiveCellsOptions
from simpeg_drivers.potential_fields.gravity.options import GravityInversionOptions
from simpeg_drivers.potential_fields.gravity.uijson import GravityInversionUIJson
from simpeg_drivers.uijson import SimPEGDriversUIJson
from simpeg_drivers.utils.testing import setup_inversion_workspace


logger = logging.getLogger(__name__)


def _current_version() -> Version:
    """Get the package version."""
    return Version(simpeg_drivers.__version__)


@pytest.fixture(name="workspace")
def workspace_fixture(tmp_path):
    """Create a workspace for testing."""
    return Workspace.create(tmp_path / "test.geoh5")


@pytest.fixture(name="simpeg_uijson_factory")
def simpeg_uijson_factory_fixture(workspace):
    """Create a SimPEGDriversUIJson object with configurable version."""

    def _create_uijson(version: str | None = None, **kwargs):
        """Create a SimPEGDriversUIJson with the given version and custom fields."""
        if version is None:
            version = _current_version().public

        return SimPEGDriversUIJson(
            version=version,
            title="My app",
            icon="",
            documentation="",
            geoh5=str(workspace.h5file),
            run_command="myapp.driver",
            monitoring_directory="",
            conda_environment="my-app",
            workspace_geoh5="",
            **kwargs,
        )

    return _create_uijson


@pytest.mark.parametrize(
    "version_input,expected",
    [
        # Normal version
        ("1.2.3", "1.2.3"),
        # Post-release version
        ("1.2.3.post1", "1.2.3"),
        # RC pre-release version
        ("1.2.3rc1", "1.2.3"),
        # Alpha pre-release version (should not normalize)
        ("1.2.3a1", "1.2.3a1"),
        # Beta pre-release version (should not normalize)
        ("1.2.3b1", "1.2.3b1"),
        # Local version
        ("1.2.3+local", "1.2.3"),
        # Combined cases
        ("1.2.3rc1.post2+local", "1.2.3"),
    ],
)
def test_comparable_version(version_input, expected):
    """Test the comparable_version method of SimPEGDriversUIJson."""
    assert SimPEGDriversUIJson.comparable_version(version_input) == expected


@pytest.mark.parametrize(
    "version_input,package_version,should_warn",
    [
        # Different version (should warn)
        ("1.0.0", "2.0.0", True),
        # Same version (should not warn)
        ("2.0.0", "2.0.0", False),
        # Post-release variant (should not warn)
        ("2.0.0.post1", "2.0.0", False),
        ("2.0.0", "2.0.0.post1", False),
        # RC variant (should not warn)
        ("2.0.0rc1", "2.0.0", False),
        ("2.0.0", "2.0.0rc1", False),
        ("2.0.0rc1", "2.0.0rc2", False),
        # differ by the pre-release number, non RC (should warn)
        ("2.0.0a1", "2.0.0a2", True),
        ("2.0.0b1", "2.0.0b2", True),
        ("2.0.0a1", "2.0.0", True),
        ("2.0.0", "2.0.0a1", True),
        ("2.0.0a1", "2.0.0b1", True),
        ("2.0.0b1", "2.0.0a1", True),
        ("2.0.0rc1", "2.0.0b1", True),
        ("2.0.0b1", "2.0.0rc1", True),
        # same normalized versions (should not warn)
        ("2.0.0-beta.1", "2.0.0b1", False),
        ("2.0.0b1", "2.0.0-beta.1", False),
    ],
)
def test_version_warning(
    monkeypatch,
    caplog,
    simpeg_uijson_factory,
    version_input,
    package_version,
    should_warn,
):
    """Test version warning behavior with mocked package version."""
    # Mock the package version
    monkeypatch.setattr(simpeg_drivers, "__version__", package_version)

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        _ = simpeg_uijson_factory(version=version_input)

        warning_message = f"version '{version_input}' does not match the current simpeg-drivers version"
        warning_found = any(
            warning_message in record.message for record in caplog.records
        )

        assert warning_found == should_warn


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

    class MyUIJson(SimPEGDriversUIJson):
        default_ui_json: ClassVar[Path] = default_path
        version: str = "0.2.0"

    MyUIJson.write_default()

    with open(default_path, encoding="utf-8") as f:
        data = json.load(f)

    # Use comparable_version for comparison to handle pre/post-release versions
    assert SimPEGDriversUIJson.comparable_version(
        data["version"]
    ) == SimPEGDriversUIJson.comparable_version(simpeg_drivers.__version__)


def test_deprecations(caplog, simpeg_uijson_factory):
    class MyUIJson(SimPEGDriversUIJson):
        my_param: Deprecated

    with caplog.at_level(logging.WARNING):
        _ = MyUIJson(**simpeg_uijson_factory().model_dump(), my_param="whoopsie")
    assert "Skipping deprecated field: my_param." in caplog.text


def test_pydantic_deprecation(simpeg_uijson_factory):
    class MyUIJson(SimPEGDriversUIJson):
        my_param: str = Field(deprecated="Use my_param2 instead.", exclude=True)

    uijson = MyUIJson(**simpeg_uijson_factory(my_param="whoopsie").model_dump())
    assert "my_param" not in uijson.model_dump()


def test_alias(simpeg_uijson_factory):
    class MyUIJson(SimPEGDriversUIJson):
        my_param: str = Field(validation_alias=AliasChoices("my_param", "myParam"))

    uijson = MyUIJson(**simpeg_uijson_factory(myParam="hello").model_dump())
    assert uijson.my_param == "hello"
    assert "myParam" not in uijson.model_fields_set
    assert "my_param" in uijson.model_dump()
    assert "myParam" not in uijson.model_dump()


def test_gravity_uijson(tmp_path):
    import warnings

    warnings.filterwarnings("error")
    geoh5, _, starting_model, survey, topography = setup_inversion_workspace(
        tmp_path, background=0.0, anomaly=0.75, inversion_type="gravity"
    )
    with geoh5.open():
        gz_channel = survey.add_data({"gz": {"values": np.ones(survey.n_vertices)}})
        gz_uncerts = survey.add_data({"gz_unc": {"values": np.ones(survey.n_vertices)}})

    opts = GravityInversionOptions(
        version="old news",
        geoh5=geoh5,
        data_object=survey,
        gz_channel=gz_channel,
        gz_uncertainty=gz_uncerts,
        mesh=starting_model.parent,
        starting_model=starting_model,
        active_cells=ActiveCellsOptions(
            topography_object=topography,
        ),
    )
    params_uijson_path = tmp_path / "from_params.ui.json"
    opts.write_ui_json(params_uijson_path)

    uijson = GravityInversionUIJson.read(params_uijson_path)
    uijson_path = tmp_path / "from_uijson.ui.json"
    uijson.write(uijson_path)
    with open(params_uijson_path, encoding="utf-8") as f:
        params_data = json.load(f)
        assert Version(params_data["version"]) == Version(_current_version().public)
    with open(uijson_path, encoding="utf-8") as f:
        uijson_data = json.load(f)

    params_data_nobraces = {}
    for param, data in params_data.items():
        if isinstance(data, dict):
            field_data_nobraces = {}
            for field, value in data.items():
                if isinstance(value, str):
                    value = value.removeprefix("{").removesuffix("}")
                if isinstance(value, list):
                    value = [v.removeprefix("{").removesuffix("}") for v in value]
                field_data_nobraces[field] = value
        else:
            field_data_nobraces = data
        params_data_nobraces[param] = field_data_nobraces

    assert uijson_data == params_data_nobraces
