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

from simpeg.maps import IdentityMap
from simpeg.objective_function import ComboObjectiveFunction
from simpeg.regularization import BaseRegularization, VectorAmplitude

from simpeg_drivers.driver import InversionDriver

from .options import MagneticVectorPDEInversionOptions


class MagneticVectorPDEInversionDriver(InversionDriver):
    """Magnetic Vector inversion driver."""

    _params_class = MagneticVectorPDEInversionOptions

    def get_regularization(self):
        if self.params.forward_only:
            return BaseRegularization(mesh=self.inversion_mesh.mesh)

        reg_funcs = []
        is_rotated = self.params.models.gradient_rotation is not None
        backward_mesh = None
        forward_mesh = None
        for mapping in self.mapping[:1]:
            reg_func = VectorAmplitude(
                forward_mesh or self.inversion_mesh.mesh,
                active_cells=self.models.active_cells if forward_mesh is None else None,
                mapping=IdentityMap(nP=self.n_values * 3),
                reference_model=self.models.reference_model,
            )

            functions = self.get_modified_regularization(
                reg_func, mapping, is_rotated, forward_mesh, backward_mesh
            )

            # Will avoid recomputing operators if the regularization mesh is the same
            forward_mesh = functions[0].regularization_mesh
            backward_mesh = functions[-1].regularization_mesh
            reg_func.objfcts = functions
            reg_func.norms = [fun.norm for fun in functions]
            reg_funcs.append(reg_func)

        return ComboObjectiveFunction(objfcts=reg_funcs)


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    MagneticVectorPDEInversionDriver.start_dask_run(file)
