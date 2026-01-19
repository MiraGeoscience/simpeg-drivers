# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np

from simpeg_drivers.utils.utils import inverse_weighted_operator, xyz_to_polar


def test_xyz_to_polar():
    """
    Test the xyz_to_polar utility function.
    """
    for _ in range(100):
        rad = np.abs(np.random.randn())
        azm = np.random.randn()

        # Create x, y, z coordinates
        x = rad * np.cos(azm)
        y = rad * np.sin(azm)
        z = np.random.randn()

        polar = xyz_to_polar(np.vstack([[[0, 0, 0]], [[x, y, z]]]))
        np.testing.assert_almost_equal(
            polar[0, 0], -polar[1, 0]
        )  # Opposite side of center
        np.testing.assert_almost_equal(polar[0, 1], polar[1, 1])  # Same azimuth
    np.testing.assert_allclose([0, z], polar[:, 2])  # Preserves z


def test_inverse_weighted_operator():
    """
    Test the inverse_weighted_operator utility function.

    For a constant input, the output should be the same constant.
    """
    power = 2.0
    threshold = 1e-12
    shape = (100, 1000)
    values = np.random.randn(shape[0] * 2)
    indices = np.c_[
        np.random.randint(0, shape[1] - 1, shape[0]),
        np.random.randint(0, shape[1] - 1, shape[0]),
    ].flatten()

    opt = inverse_weighted_operator(values, indices, shape, power, threshold)
    test_val = np.random.randn()
    interp = opt * np.full(shape[1], test_val)

    assert opt.shape == shape
    np.testing.assert_allclose(interp, test_val, rtol=1e-3)
