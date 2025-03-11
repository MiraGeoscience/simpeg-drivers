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
from geoh5py import Workspace

from simpeg_drivers.params import ActiveCellsOptions
from simpeg_drivers.potential_fields.gravity.params import GravityInversionOptions
from simpeg_drivers.potential_fields.gravity.uijson import GravityInversionUIJson
from simpeg_drivers.uijson import SimPEGDriversUIJson
from simpeg_drivers.utils.testing import setup_inversion_workspace


logger = logging.getLogger(__name__)


def test_version_warning(tmp_path, caplog):
    workspace = Workspace(tmp_path / "test.geoh5")

    with caplog.at_level(logging.WARNING):
        _ = SimPEGDriversUIJson(
            version="0.2.0",
            title="My app",
            icon="",
            documentation="",
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

    class MyUIJson(SimPEGDriversUIJson):
        default_ui_json: ClassVar[Path] = default_path
        version: str = "0.2.0"

    MyUIJson.write_default()

    with open(default_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "0.3.0-alpha.1"


def test_gravity_uijson(tmp_path):
    geoh5, _, starting_model, survey, topography = setup_inversion_workspace(
        tmp_path, background=0.0, anomaly=0.75, inversion_type="gravity"
    )

    opts = GravityInversionOptions(
        geoh5=geoh5,
        data_object=survey,
        gz_channel=survey.add_data({"gz": {"values": np.ones(survey.n_vertices)}}),
        gz_uncertainty=survey.add_data(
            {"gz_unc": {"values": np.ones(survey.n_vertices)}}
        ),
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


def test_field_handling():
    # TODO: This is was for prototyping and should be removed once the
    # behaviours tested here are incorporated into the UIJson classes.

    import warnings
    from typing import Annotated, Any

    from pydantic import AliasChoices, BaseModel, BeforeValidator, Field

    def deprecate(value, info):
        warnings.warn(  # will be a logging.warn in production
            f"Field {info.field_name} is deprecated."
        )
        return value

    Deprecated = Annotated[
        Any,
        Field(exclude=True),
        BeforeValidator(deprecate),
    ]

    class MyClass(BaseModel):
        a: int = 1  # Represents a newly added field with a default value.
        b: int = Field(  # Represents a field with a name change.
            validation_alias=AliasChoices("b", "bb")
        )
        c: Deprecated  # Represents a deprecated field.

    test = MyClass(bb=2, c=3)
    assert test.a == 1
    assert test.b == 2

    dump = test.model_dump()
    assert "c" not in dump
    assert "b" in dump
    assert "bb" not in dump
    assert dump["a"] == 1
