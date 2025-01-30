# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# pylint: disable=redefined-outer-name

from __future__ import annotations

import pytest
from geoh5py.objects import DrapeModel
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
from simpeg_drivers.params import ActiveCellsData
from simpeg_drivers.potential_fields import (
    GravityInversionParams,
    MagneticScalarInversionParams,
    MagneticVectorInversionParams,
)
from simpeg_drivers.utils.testing import setup_inversion_workspace


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
