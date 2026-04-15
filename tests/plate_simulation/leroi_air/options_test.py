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
from geoapps_utils.modelling.plates import PlateModel
from geoh5py import Workspace

from . import generate_plate_options


def test_options(tmp_path):

    with Workspace(tmp_path / "test.geoh5") as geoh5:
        opts = generate_plate_options(workspace=geoh5)

    assert np.allclose(opts.channel_widths, [0.3, 0.3, 0.6])
    assert np.isclose(opts.frequency, 0.142857143)
    assert np.isclose(opts.offtime, 1.6)
    assert np.allclose(opts.ontime_waveform, opts.waveform[0:8, :])
    assert np.allclose(
        opts.conductivity_thicknesses, np.array([0.0333333, 0.5, 0.4, 0.1])
    )
