# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
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

from simpeg_drivers.depth_of_investigation.sensitivity_cutoff.options import (
    SensitivityCutoffOptions,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lower_percentile_mask(data: np.ndarray, cutoff: float) -> np.ndarray:
    """
    Create mask for data to remove lower percentile values.

    :param data: Data.
    :param cutoff: lower percentile below which the mask will filter values.
    """
    finite_data = data[~np.isnan(data)]
    cutoff_value = np.percentile(finite_data, cutoff)
    mask = data > cutoff_value

    return mask


def lower_percent_mask(data: np.ndarray, cutoff: float, logspace=False) -> np.ndarray:
    """
    Create mask for data to remove bottom ten percent of normalized values.

    :param data: Data.
    :param cutoff: Data are normalized into the range [0, 100] so that the
        cutoff value eliminates the bottom n percent of data.
    :param logspace: Applies cutoff on log10(data).
    """

    if logspace:
        data[data == 0] = np.nan
        data = np.log10(data)
        data -= np.nanmin(data)

    scaled_data = data * 100 / np.nanmax(data)
    mask = scaled_data > cutoff

    return mask


def sensitivity_mask(
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
        mask = lower_percentile_mask(values, cutoff)
    elif method == "percent":
        mask = lower_percent_mask(values, cutoff)
    elif method == "log_percent":
        mask = lower_percent_mask(values, cutoff, logspace=True)
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

    _params_class = SensitivityCutoffOptions

    def __init__(self, params: SensitivityCutoffOptions):
        super().__init__(params)

    def run(self):
        logger.info("Scaling sensitivities . . .")
        mask = sensitivity_mask(
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
