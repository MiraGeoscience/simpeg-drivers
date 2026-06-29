# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.objects import DrapeModel, Octree
from simpeg.maps import Projection
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import BaseRegularization, VectorAmplitude

from simpeg_drivers.driver import InversionDriver, first_child_of_type
from simpeg_drivers.potential_fields.magnetic_vector_pde.options import (
    MagneticVectorPDEInversionOptions,
)


class MagneticVectorPDEInversionDriver(InversionDriver):
    """Magnetic Vector inversion driver."""

    _params_class = MagneticVectorPDEInversionOptions

    def get_regularization(self):
        if self.params.forward_only:
            return BaseRegularization(mesh=self.inversion_mesh.mesh)

        reg_funcs = []
        is_rotated = self.params.models.gradient_rotation is not None
        indices = np.hstack([mapping.P.indices for mapping in self.mapping])
        mapping = Projection(self.mapping[0].shape[1], indices)
        reg_func = VectorAmplitude(
            self.inversion_mesh.mesh,
            active_cells=self.models.active_cells,
            mapping=mapping,
            reference_model=self.models.reference_model,
        )

        functions = self.get_modified_regularization(
            reg_func, self.mapping[0], is_rotated, None, None
        )
        reg_func.objfcts = functions
        reg_func.norms = [fun.norm for fun in functions]
        reg_funcs.append(reg_func)

        return ComboObjectiveFunction(objfcts=reg_funcs)

    def _reset_models(self, iteration):
        """
        Reset the inversion models based on specified iteration and mesh.

        :param iteration: The iteration number to reset the models for.
        :param mesh: The mesh to reset the models from.
        """
        mesh = first_child_of_type(self.out_group, (DrapeModel, Octree))
        flag = f"Iteration_{iteration}_"
        count = 0
        for child in mesh.children:
            if flag not in child.name:
                continue

            if "amplitude" in child.name:
                self.params.models.starting_model = child
            else:
                name = "starting_" + child.name.split("_")[2]
                setattr(self.params.models, name, child)
            count += 1

            if count == 3:
                return

        if count != 3:
            raise GeoAppsError(
                f"Could not reset the inversion at iteration {iteration}, no models found."
            )


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    MagneticVectorPDEInversionDriver.start_dask_run(file)
