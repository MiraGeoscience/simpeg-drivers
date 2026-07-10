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

from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.objects import DrapeModel, Octree

from simpeg_drivers.driver import InversionDriver, first_child_of_type
from simpeg_drivers.potential_fields.magnetic_vector.options import (
    MagneticVectorInversionOptions,
)
from simpeg_drivers.utils.utils import argument_parser


class MagneticVectorInversionDriver(InversionDriver):
    """Magnetic Vector inversion driver."""

    _params_class = MagneticVectorInversionOptions

    def _reset_models(self, iteration: int):
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
    file, args = argument_parser()
    MagneticVectorInversionDriver.start_dask_run(file, **args)
