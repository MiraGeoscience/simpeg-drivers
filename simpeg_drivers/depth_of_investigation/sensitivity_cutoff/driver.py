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

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.params import (
    SensitivityCutoffParams,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def apply_cutoff(
    sensitivity: FloatData, cutoff: float, method: str = "percentile"
) -> np.ndarray:
    """
    Create cutoff mask for one of 'percentile', 'percent', or 'log_percent' methods.

    :param sensitivity: Sensitivity data object.
    :param cutoff: Cutoff value.
    :param method: Cutoffs methods can be lower 'percentile', 'percent', or 'log_percent'.
    """
    values = sensitivity.values.copy()

    if method == "percentile":
        finite_values = values[~np.isnan(values)]
        cutoff_value = np.percentile(finite_values, cutoff)
        mask = values > cutoff_value
    elif method == "percent":
        scaled_sensitivity = values * 100 / np.nanmax(values)
        mask = scaled_sensitivity > cutoff
    elif method == "log_percent":
        log_values = np.log10(values + 1)
        scaled_sensitivity = log_values * 100 / np.nanmax(log_values)
        mask = scaled_sensitivity > cutoff
    else:
        raise ValueError(
            "Invalid method. Must be 'percentile', 'percent', or 'log_percent'."
        )

    return mask


class SensitivityCutoffDriver(BaseDriver):
    """
    Creates a mask to filter sensitivities below a cutoff value.

    Sensitivities will be normalized by cell volumes and scaled as a
    percentage.  A mask will then be created to filter out sensitivities
    below the provided cutoff percentage.
    """

    _params_class = SensitivityCutoffParams

    def __init__(self, params: SensitivityCutoffParams):
        super().__init__(params)

    def run(self):
        logger.info("Scaling sensitivities . . .")
        mask = apply_cutoff(
            self.params.sensitivity_model,
            self.params.sensitivity_cutoff,
            self.params.cutoff_method,
        )
        logger.info("Creating cutoff mask '%s'", self.params.mask_name)
        cutoff_mask = self.params.mesh.add_data(
            {f"{self.params.mask_name}": {"values": mask, "association": "CELL"}}
        )

        self.update_monitoring_directory(self.params.mesh)

        return cutoff_mask


if __name__ == "__main__":
    file = sys.argv[1]
    SensitivityCutoffDriver.start(file)
