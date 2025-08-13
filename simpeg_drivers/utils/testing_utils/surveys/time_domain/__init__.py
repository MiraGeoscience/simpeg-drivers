# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of geoapps-utils package.                                      '
#                                                                                   '
#  geoapps-utils is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np


channels = np.r_[3e-04, 6e-04, 1.2e-03] * 1e3
waveform = np.c_[
    np.r_[
        np.arange(-0.002, -0.0001, 5e-4),
        np.arange(-0.0004, 0.0, 1e-4),
        np.arange(0.0, 0.002, 5e-4),
    ]
    * 1e3
    + 2.0,
    np.r_[np.linspace(0, 1, 4), np.linspace(0.9, 0.0, 4), np.zeros(4)],
]
