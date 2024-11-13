# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.driver.driver import BaseDriver
from geoh5py.data import FloatData
from geoh5py.objects import Octree

from .params import SensitivityCutoffParams


def scale_sensitivity(sensitivity: FloatData) -> np.ndarray:
    """
    Normalize sensitivities by cell sizes and scale as percentage.

    :param sensitivity: Sum squared sensitivity matrix.
    """
    mesh = sensitivity.parent
    cell_sizes = (
        mesh.octree_cells["NCells"]
        * mesh.u_cell_size
        * mesh.octree_cells["NCells"]
        * mesh.v_cell_size
        * mesh.octree_cells["NCells"]
        * mesh.w_cell_size
    )
    out = sensitivity.values / cell_sizes
    out *= 100 / np.max(out)

    return out


class SensitivityCutoffDriver(BaseDriver):
    def __init__(self, params: SensitivityCutoffParams):
        super().__init__(params)

    def run(self):
        scaled_sensitivity = scale_sensitivity(self.params.sensitivity_model)
        cutoff_mask = self.params.mesh.add_data(
            {
                "sensitivity_cutoff": {
                    "association": "CELL",
                    "values": scaled_sensitivity > self.params.sensitivity_cutoff,
                }
            }
        )

        return cutoff_mask
