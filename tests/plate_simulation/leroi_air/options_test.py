# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.groups import SimPEGGroup
from pydantic import ValidationError

from simpeg_drivers.plate_simulation.leroi_air.options import LeroiAirOptions

from . import generate_plate_options


def test_options_channel_widths(plate_options):
    assert np.allclose(plate_options.survey.channel_widths, [0.3, 0.3, 0.6])


def test_options_channel_widths_from_metadata(tmp_path):
    explicit_widths = [0.1, 0.2, 0.3]
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(workspace=geoh5)
        meta = opts.survey.entity.metadata
        meta["channel_widths"] = explicit_widths
        opts.survey.entity.metadata = meta

    assert np.allclose(opts.survey.channel_widths, explicit_widths)


def test_options_frequency(plate_options):
    assert np.isclose(plate_options.survey.frequency, 142.857143)


def test_options_frequency_from_metadata(tmp_path):
    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(workspace=geoh5)
        meta = opts.survey.entity.metadata
        meta["frequency"] = 0.15
        opts.survey.entity.metadata = meta

    assert np.isclose(opts.survey.frequency, 0.15)


def test_options_offtime(plate_options):
    assert np.isclose(plate_options.survey.offtime, 1.6)


def test_options_ontime_waveform(plate_options):
    assert np.allclose(
        plate_options.survey.ontime_waveform,
        plate_options.survey.entity.waveform[0:8, :],
    )


def test_options_conductivity_thicknesses(plate_options):
    assert np.allclose(
        plate_options.conductivity_thicknesses, np.array([0.0333333, 0.5, 0.4, 0.1])
    )


def test_options_resistivities(plate_options):
    assert np.allclose(plate_options.resistivities, [1500.0, 2000.0, 5000.0, 100.0])


def test_options_drape_height(plate_options):
    assert np.allclose(plate_options.survey.drape_height(plate_options.topo), 20.0)


def test_options_validate_layer_lengths_mismatch(plate_options):
    ws = Workspace()
    out_group = SimPEGGroup.create(ws)
    with pytest.raises(ValidationError, match="layer_resistivities"):
        LeroiAirOptions(
            survey=plate_options.survey,
            topo=plate_options.topo,
            layer_resistivities=[1500.0],
            layer_thicknesses=[50.0, 1000.0],
            plate_resistivities=plate_options.plate_resistivities,
            plate_geometries=plate_options.plate_geometries,
            out_group=out_group,
        )


def test_options_validate_plate_lengths_mismatch(plate_options):
    ws = Workspace()
    out_group = SimPEGGroup.create(ws)
    with pytest.raises(ValidationError, match="plate_resistivities"):
        LeroiAirOptions(
            survey=plate_options.survey,
            topo=plate_options.topo,
            layer_resistivities=plate_options.layer_resistivities,
            layer_thicknesses=plate_options.layer_thicknesses,
            plate_resistivities=[100.0, 200.0],
            plate_geometries=plate_options.plate_geometries,
            out_group=out_group,
        )
