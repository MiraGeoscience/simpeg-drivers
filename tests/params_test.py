# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                     '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=redefined-outer-name

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from geoh5py.shared.exceptions import (
    AssociationValidationError,
    OptionalValidationError,
    RequiredValidationError,
    ShapeValidationError,
    TypeValidationError,
    UUIDValidationError,
    ValueValidationError,
)
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import requires_value

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DirectCurrent3DParams,
)
from simpeg_drivers.electricals.induced_polarization.three_dimensions import (
    InducedPolarization3DParams,
)
from simpeg_drivers.potential_fields import (
    GravityParams,
    MagneticScalarParams,
    MagneticVectorParams,
)
from simpeg_drivers.utils.testing import setup_inversion_workspace


@pytest.fixture(scope="session")
def mvi_params(tmp_path_factory):
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path_factory.mktemp("mvi"),
        background=0.01,
        anomaly=10,
        n_electrodes=2,
        n_lines=2,
        flatten=False,
    )
    geoh5.close()
    inducing_field = (50000.0, 90.0, 0.0)
    params = MagneticVectorParams(
        geoh5=geoh5,
        mesh=model.parent.uid,
        topography_object=topography.uid,
        inducing_field_strength=inducing_field[0],
        inducing_field_inclination=inducing_field[1],
        inducing_field_declination=inducing_field[2],
        z_from_topo=False,
        data_object=survey.uid,
        starting_model_object=model.parent.uid,
        starting_model=model.uid,
        starting_inclination=45,
        starting_declination=270,
    )
    params.input_file.geoh5.open()

    return params


@pytest.fixture(scope="session")
def grav_params(tmp_path_factory):
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path_factory.mktemp("gravity"),
        background=0.01,
        anomaly=10,
        n_electrodes=2,
        n_lines=2,
        flatten=False,
    )
    geoh5.close()
    params = GravityParams(
        **{
            "geoh5": geoh5,
            "data_object": survey,
            "topography_object": topography,
            "mesh": mesh,
        }
    )
    params.input_file.geoh5.open()

    return params


@pytest.fixture(scope="session")
def dc_params(tmp_path_factory):
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path_factory.mktemp("dcr"),
        background=0.01,
        anomaly=10,
        n_electrodes=2,
        n_lines=2,
        inversion_type="dcip",
        flatten=False,
    )

    geoh5.close()

    params = DirectCurrent3DParams(
        **{
            "geoh5": geoh5,
            "data_object": survey,
            "topography_object": topography,
            "mesh": mesh,
        }
    )
    params.input_file.geoh5.open()

    return params


@pytest.fixture(scope="session")
def ip_params(tmp_path_factory):
    geoh5, mesh, model, survey, topography = setup_inversion_workspace(
        tmp_path_factory.mktemp("dcr"),
        background=0.01,
        anomaly=10,
        n_electrodes=2,
        n_lines=2,
        inversion_type="dcip",
        flatten=False,
    )
    geoh5.close()
    ip_params = InducedPolarization3DParams(
        **{
            "geoh5": geoh5,
            "data_object": survey,
            "topography": topography,
            "mesh": mesh,
        }
    )
    ip_params.input_file.geoh5.open()

    return ip_params


def catch_invalid_generator(params, field, invalid_value, validation_type):
    if validation_type == "value":
        err = ValueValidationError
    elif validation_type == "type":
        err = TypeValidationError
    elif validation_type == "shape":
        err = ShapeValidationError
    elif validation_type == "required":
        err = RequiredValidationError
    elif validation_type == "uuid":
        err = UUIDValidationError
    elif validation_type == "association":
        err = AssociationValidationError

    with pytest.raises(err):
        setattr(params, field, invalid_value)


def param_test_generator(params, param, value):
    setattr(params, param, value)
    pval = params.input_file.data[param]
    if hasattr(pval, "uid"):
        pval = pval.uid

    assert pval == value


def test_write_input_file_validation(tmp_path, mvi_params):
    test_dict = mvi_params.to_dict()
    test_dict.pop("topography_object")
    params = MagneticVectorParams(**test_dict)  # pylint: disable=repeated-keyword

    with pytest.raises(OptionalValidationError, match="topography_object"):
        params.write_input_file(name="test.ui.json", path=tmp_path)


def test_params_initialize():
    for params in [
        MagneticScalarParams(),
        MagneticVectorParams(),
        GravityParams(),
        DirectCurrent3DParams(),
        InducedPolarization3DParams(),
    ]:
        check = []
        for k, v in params.defaults.items():
            if " " in k or k in [
                "starting_model",
                "conductivity_model",
                "min_value",
            ]:
                continue
            check.append(getattr(params, k) == v)
        assert all(check)

    params = MagneticVectorParams(starting_model=1.0)
    assert params.starting_model == 1.0
    params = GravityParams(starting_model=1.0)
    assert params.starting_model == 1.0


def test_input_file_construction(tmp_path: Path):
    params_classes = [
        GravityParams,
        MagneticScalarParams,
        MagneticVectorParams,
        DirectCurrent3DParams,
        InducedPolarization3DParams,
    ]

    for params_class in params_classes:
        filename = "test.ui.json"
        for forward_only in [True, False]:
            params = params_class(forward_only=forward_only)
            params.write_input_file(name=filename, path=tmp_path, validate=False)
            ifile = InputFile.read_ui_json(tmp_path / filename, validate=False)
            params = params_class(input_file=ifile)

            check = []
            for k, v in params.defaults.items():
                # TODO Need to better handle defaults None to value
                if (" " in k) or k in [
                    "starting_model",
                    "reference_model",
                    "conductivity_model",
                    "min_value",
                ]:
                    continue
                check.append(getattr(params, k) == v)

            assert all(check)


def test_default_input_file(tmp_path: Path):
    for params_class in [
        MagneticScalarParams,
        MagneticVectorParams,
        GravityParams,
        DirectCurrent3DParams,
        InducedPolarization3DParams,
    ]:
        filename = "test.ui.json"
        params = params_class()
        params.write_input_file(name=filename, path=tmp_path, validate=False)
        ifile = InputFile.read_ui_json(tmp_path / filename, validate=False)

        # check that reads back into input file with defaults
        check = []
        for k, v in ifile.data.items():
            if " " in k or requires_value(ifile.ui_json, k):
                continue
            check.append(v == params.defaults[k])
        assert all(check)

        # check that params constructed from_path is defaulted
        params2 = params_class()
        check = []
        for k, v in params2.to_dict(ui_json_format=False).items():
            if " " in k or requires_value(ifile.ui_json, k):
                continue
            check.append(v == ifile.data[k])
        assert all(check)


def test_update():
    new_params = {
        "starting_model": 99.0,
    }
    params = MagneticVectorParams()
    params.update(new_params)
    assert params.starting_model == 99.0


def test_chunk_validation_mvi(tmp_path, mvi_params):
    test_dict = mvi_params.to_dict()
    test_dict.pop("data_object")
    params = MagneticVectorParams(**test_dict)  # pylint: disable=repeated-keyword
    with pytest.raises(
        RequiredValidationError, match="Missing required parameter: 'data_object'"
    ):
        params.write_input_file(name="test.ui.json", path=tmp_path)


def test_chunk_validation_mag(tmp_path: Path, mvi_params):
    test_dict = mvi_params.to_dict()
    test_dict["inducing_field_strength"] = None
    params = MagneticVectorParams(**test_dict)
    with pytest.raises(
        OptionalValidationError,
        match="Cannot set a None value to non-optional parameter: inducing_field_strength.",
    ):
        params.write_input_file(name="test.ui.json", path=tmp_path)


def test_chunk_validation_grav(tmp_path: Path, grav_params):
    test_dict = grav_params.to_dict()
    params = GravityParams(**test_dict)  # pylint: disable=repeated-keyword
    params.topography_object = None
    with pytest.raises(
        OptionalValidationError,
        match="Cannot set a None value to non-optional parameter: topography_object.",
    ):
        params.write_input_file(name="test.ui.json", path=tmp_path)


def test_active_set(mvi_params):
    assert "inversion_type" in mvi_params.active_set()
    assert "mesh" in mvi_params.active_set()


def test_validate_inversion_type(mvi_params):
    param = "inversion_type"
    newval = "magnetic vector"
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, "em", "value")


def test_validate_inducing_field_strength(mvi_params):
    param = "inducing_field_strength"
    newval = 60000.0
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, "test", "type")


def test_validate_inducing_field_inclination(mvi_params):
    param = "inducing_field_inclination"
    newval = 44.0
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, "test", "type")


def test_validate_inducing_field_declination(mvi_params):
    param = "inducing_field_declination"
    newval = 9.0
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, "test", "type")


def test_validate_topography_object(mvi_params):
    param = "topography_object"
    newval = UUID("{79b719bc-d996-4f52-9af0-10aa9c7bb941}")
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, True, "type")
    catch_invalid_generator(mvi_params, param, "lsdkfj", "uuid")
    catch_invalid_generator(mvi_params, param, "", "uuid")


def test_validate_topography(mvi_params):
    param = "topography"
    newval = UUID("{79b719bc-d996-4f52-9af0-10aa9c7bb941}")
    catch_invalid_generator(mvi_params, param, newval, "association")
    newval = "abc"
    catch_invalid_generator(mvi_params, param, newval, "uuid")


def test_validate_data_object(mvi_params):
    param = "data_object"
    newval = uuid4()
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, 2, "type")


def test_validate_starting_model(mvi_params):
    param = "starting_model"
    param_test_generator(mvi_params, param, 1.0)
    newval = uuid4()
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, {}, "type")


def test_validate_starting_inclination(mvi_params):
    param = "starting_inclination"
    param_test_generator(mvi_params, param, 1.0)
    newval = uuid4()
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, {}, "type")


def test_validate_starting_declination(mvi_params):
    param = "starting_declination"
    param_test_generator(mvi_params, param, 1.0)
    newval = uuid4()
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, {}, "type")


def test_validate_tile_spatial(mvi_params):
    param = "tile_spatial"
    newval = 9
    invalidval = {}
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, invalidval, "type")


def test_validate_receivers_radar_drape(mvi_params):
    param = "receivers_radar_drape"
    newval = uuid4()
    catch_invalid_generator(mvi_params, param, newval, "association")
    catch_invalid_generator(mvi_params, param, {}, "type")


@pytest.mark.parametrize(
    "param,newval,value,error_type",
    [
        ("receivers_offset_z", 99.0, "test", "type"),
        ("max_chunk_size", 256, "asdf", "type"),
        ("chunk_by_rows", True, "sdf", "type"),
        ("output_tile_files", True, "sdf", "type"),
        ("inversion_style", "voxel", 123, "type"),
        ("chi_factor", 0.5, "test", "type"),
        ("sens_wts_threshold", 0.1, "test", "type"),
        ("every_iteration_bool", True, "test", "type"),
        ("f_min_change", 1e-3, "test", "type"),
        ("beta_tol", 0.2, "test", "type"),
        ("prctile", 90, "test", "type"),
        ("coolingRate", 3, "test", "type"),
        ("coolingFactor", 4.0, "test", "type"),
        ("coolEps_q", False, "test", "type"),
        ("coolEpsFact", 1.1, "test", "type"),
        ("beta_search", True, "test", "type"),
        ("starting_chi_factor", 2.0, "test", "type"),
        ("max_global_iterations", 2, "test", "type"),
        ("max_irls_iterations", 1, "test", "type"),
        ("max_cg_iterations", 2, "test", "type"),
        ("initial_beta", 2.0, "test", "type"),
        ("initial_beta_ratio", 0.5, "test", "type"),
        ("tol_cg", 0.1, "test", "type"),
        ("alpha_s", 0.1, "test", "type"),
        ("length_scale_x", 0.1, "test", "type"),
        ("length_scale_y", 0.1, "test", "type"),
        ("length_scale_z", 0.1, "test", "type"),
        ("s_norm", 0.5, "test", "type"),
        ("x_norm", 0.5, "test", "type"),
        ("y_norm", 0.5, "test", "type"),
        ("z_norm", 0.5, "test", "type"),
        ("reference_model", 99.0, {}, "type"),
        ("reference_inclination", 99.0, {}, "type"),
        ("reference_declination", 99.0, {}, "type"),
        ("gradient_type", "components", "test", "value"),
        ("lower_bound", -1000, {}, "type"),
        ("upper_bound", 1000, {}, "type"),
        ("parallelized", False, "test", "type"),
        ("n_cpu", 12, "test", "type"),
    ],
)
def test_validate_inversion_parameters(
    mvi_params, param, newval, value, error_type
):  # pylint: disable=expression-not-assigned
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, value, error_type),


def test_validate_geoh5(mvi_params):
    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'Path', 'Workspace', 'NoneType'.",
    ):
        mvi_params.geoh5 = 4


def test_validate_out_group(mvi_params):
    param = "out_group"
    newval = "test_"
    with pytest.raises(UUIDValidationError, match="not a valid uuid string"):
        param_test_generator(mvi_params, param, newval)


def test_validate_distributed_workers(mvi_params):
    param = "distributed_workers"
    newval = "one, two"
    param_test_generator(mvi_params, param, newval)
    catch_invalid_generator(mvi_params, param, 123, "type")


@pytest.mark.parametrize(
    "channel", ["tmi", "bx", "by", "bz", "bxy", "bxz", "byz", "bxx", "byy", "bzz"]
)
def test_mag_data(mvi_params, channel):
    with pytest.raises(AssociationValidationError):
        setattr(mvi_params, f"{channel}_channel", uuid4())

    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'Entity', 'NoneType'.",
    ):
        setattr(mvi_params, f"{channel}_channel", 4)

    with pytest.raises(AssociationValidationError):
        setattr(mvi_params, f"{channel}_uncertainty", uuid4())

    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'int', 'float', 'Entity', 'NoneType'.",
    ):
        setattr(mvi_params, f"{channel}_uncertainty", mvi_params.geoh5)


def test_gravity_inversion_type(grav_params):
    with pytest.raises(
        ValueValidationError, match="'inversion_type' is invalid. Must be: 'gravity'"
    ):
        grav_params.inversion_type = "alskdj"


@pytest.mark.parametrize(
    "channel", ["gz", "gy", "gz", "guv", "gxy", "gxz", "gyz", "gxx", "gyy", "gzz"]
)
def test_grav_data(grav_params, channel):
    with pytest.raises(AssociationValidationError):
        setattr(grav_params, f"{channel}_channel", uuid4())

    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'Entity', 'NoneType'.",
    ):
        setattr(grav_params, f"{channel}_channel", 4)

    with pytest.raises(AssociationValidationError):
        setattr(grav_params, f"{channel}_uncertainty", uuid4())

    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'int', 'float', 'Entity', 'NoneType'.",
    ):
        setattr(grav_params, f"{channel}_uncertainty", grav_params.geoh5)


def test_direct_current_inversion_type(dc_params):
    with pytest.raises(ValueValidationError, match="Must be: 'direct current 3d'"):
        dc_params.inversion_type = "alskdj"


def test_direct_current_data_object(dc_params):
    with pytest.raises(
        TypeValidationError, match="Must be one of: 'UUID', 'PotentialElectrode'."
    ):
        dc_params.data_object = 4


def test_potential_channel(dc_params):
    with pytest.raises(
        TypeValidationError, match="Must be one of: 'str', 'UUID', 'Entity'."
    ):
        dc_params.potential_channel = 4


def test_potential_uncertainty(dc_params):
    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'int', 'float', 'Entity'.",
    ):
        dc_params.potential_uncertainty = dc_params.geoh5


def test_induced_polarization_inversion_type(ip_params):
    with pytest.raises(
        ValueValidationError, match="Must be: 'induced polarization 3d'"
    ):
        ip_params.inversion_type = "alskdj"


def test_chargeability_channel(ip_params):
    with pytest.raises(
        TypeValidationError, match="Must be one of: 'str', 'UUID', 'Entity'."
    ):
        ip_params.chargeability_channel = 4


def test_chargeability_uncertainty(ip_params):
    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'int', 'float', 'Entity'.",
    ):
        ip_params.chargeability_uncertainty = ip_params.geoh5


def test_conductivity_model(ip_params):
    with pytest.raises(
        TypeValidationError,
        match="Must be one of: 'str', 'UUID', 'int', 'float', 'Entity'.",
    ):
        ip_params.conductivity_model = ip_params.geoh5
