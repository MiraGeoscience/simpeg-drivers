# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

from geoh5py import Workspace

from simpeg_drivers.plate_simulation.models.options import PlateOptions

from .interface import LeroiAirInterface
from .options import BackgroundOptions, LeroiAirOptions, ModellingOptions, OutputOptions


class LeroiAirDriver:
    def __init__(self, options: LeroiAirOptions):
        self.options = options

    def run(self):
        opts = LeroiAirOptions(
            title="test",
            background=BackgroundOptions(
                basement_thickness=5000,
                basement_resistivity=1000,
            ),
            modelling=ModellingOptions(offtime=3.1, cell_size=10),
            output=OutputOptions(channel="all")
        )

        with Workspace("dom_waveform_600Ohmm_bkgr_and_plate.geoh5", mode="r") as geoh5:
            survey = geoh5.get_entity("survey")[1]
            plate = PlateOptions(
                reference=[0.0, 0.0, -20.0],
                strike_length=80.,
                dip_length=100.,
                thickness=5.,
                dip_direction=90.,
                dip=90.,
                resistivity=1.,
            )
            interface = LeroiAirInterface(geoh5, survey, plate, opts)

        interface.format_cfl_file()
        interface.write_cfl_file(Path('LeroiAir.cfl'))