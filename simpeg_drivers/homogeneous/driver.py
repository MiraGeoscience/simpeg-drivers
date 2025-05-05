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
from pathlib import Path

import numpy as np
from geoh5py.data import ReferencedData
from simpeg.maps import SurjectUnits

from simpeg_drivers.components.models import InversionModel
from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.homogeneous.options import HomogeneousOptions
from simpeg_drivers.utils.utils import simpeg_group_to_driver


logger = logging.getLogger(__name__)


class HomogeneousDriver(InversionDriver):
    """
    Class to invert for the mean physical property of geological units.
    """

    _options_class = HomogeneousOptions

    def __init__(self, params: HomogeneousOptions):
        self._driver: InversionDriver | None = None
        self._mesh: TreeMesh | None = None
        self._geo_model: ReferencedData | None = None

        super().__init__(params)

    @property
    def driver(self) -> InversionDriver:
        """
        Return the driver instance.
        """
        if self._driver is None:
            self._driver = simpeg_group_to_driver(
                self.params.inversion_group, self.params.geoh5
            )

        return self._driver

    @property
    def data_misfit(self):
        """
        Modify the misfits of internal driver.
        """

    @property
    def optimization(self):
        if getattr(self, "_optimization", None) is None:
            if self.params.forward_only:
                return optimization.ProjectedGNCG()

            self._optimization = optimization.ProjectedGNCG(
                maxIter=self.params.max_global_iterations,
                lower=self.models.lower_bound,
                upper=self.models.upper_bound,
                maxIterLS=self.params.max_line_search_iterations,
                maxIterCG=self.params.max_cg_iterations,
                tolCG=self.params.tol_cg,
                stepOffBoundsFact=1e-8,
                LSshorten=0.25,
            )
        return self._optimization

    @property
    def regularization(self):
        if getattr(self, "_regularization", None) is None:
            with fetch_active_workspace(self.workspace, mode="r"):
                self._regularization = self.get_regularization()

        return self._regularization

    def run(self):
        units = InversionModel.obj_2_mesh(
            self.params.geo_model, self.driver.inversion_mesh.entity
        )
        units = units[self.driver.models.active_cells]

        active_units = []
        for unit in np.unique(units):
            active_units.append(units == unit)

        mapping = SurjectUnits(active_units)
        mesh = TensorMesh(np.ones(mapping.nP))
        reference_model = (
            mapping.P.T @ self.driver.models.reference / mapping.P.sum(axis=0)
        )
        self.driver.regularization

        for name in self.driver.models.model_types:
            mod = getattr(self.driver.models, name, None)

        print(units)


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    HomogeneousDriver.start(file)
