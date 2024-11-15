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

import logging
import sys

import numpy as np
from geoapps_utils.driver.driver import BaseDriver
from geoh5py.data import FloatData
from geoh5py.objects import Octree
from geoh5py.shared.utils import fetch_active_workspace

from .params import SensitivityCutoffParams


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    out *= 100 / np.nanmax(out)

    return out


class SensitivityCutoffDriver(BaseDriver):
    _params_class = SensitivityCutoffParams

    def __init__(self, params: SensitivityCutoffParams):
        super().__init__(params)

    def run(self):
        logger.info("Scaling sensitivities . . .")
        scaled_sensitivity = scale_sensitivity(self.params.sensitivity_model)
        logger.info("Creating cutoff mask '%s'", self.params.mask_name)
        cutoff_mask = self.params.mesh.add_data(
            {
                f"{self.params.mask_name} (mask)": {
                    "association": "CELL",
                    "values": scaled_sensitivity > self.params.sensitivity_cutoff,
                },
                f"{self.params.mask_name} (scaled sensitivities)": {
                    "association": "CELL",
                    "values": scaled_sensitivity,
                },
            }
        )

        self.update_monitoring_directory(self.params.mesh)

        return cutoff_mask


if __name__ == "__main__":
    file = sys.argv[1]
    SensitivityCutoffDriver.start(file)
