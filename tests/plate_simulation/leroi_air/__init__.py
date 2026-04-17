# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import numpy as np
from geoapps_utils.modelling.plates import PlateModel
from geoh5py.shared.utils import fetch_active_workspace

from simpeg_drivers.plate_simulation.leroi_air.options import LeroiAirOptions
from simpeg_drivers.utils.synthetics.surveys.time_domain.airborne_tdem import (
    generate_airborne_tdem_survey,
)


def generate_plate_options(workspace):
    x = np.linspace(-1000, 1000, 81)
    y = np.linspace(-1000, 1000, 81)
    X, Y = np.meshgrid(x, y)
    Z = np.full_like(X, 20.0)

    with fetch_active_workspace(workspace) as geoh5:
        survey = generate_airborne_tdem_survey(geoh5, X=X, Y=Y, Z=Z)
        layer_resistivities = [1500.0, 2000.0, 5000.0]
        layer_thicknesses = [50.0, 1000.0, 2000.0]
        plate_resistivities = [100.0]
        plate_geometries = [
            PlateModel(
                strike_length=200,
                dip_length=100,
                width=10,
                direction=90,
                dip=45,
            )
        ]
        topo = np.column_stack([X.flatten(), Y.flatten(), np.zeros(X.size)])
        opts = LeroiAirOptions(
            survey=survey,
            topo=topo,
            layer_resistivities=layer_resistivities,
            layer_thicknesses=layer_thicknesses,
            plate_resistivities=plate_resistivities,
            plate_geometries=plate_geometries,
        )
        return opts
