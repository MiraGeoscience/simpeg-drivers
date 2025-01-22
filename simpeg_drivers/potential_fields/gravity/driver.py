# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from simpeg_drivers.driver import InversionDriver

from .constants import validations
from .params import GravityForwardParams, GravityInversionParams
from geoapps_utils.driver.data import BaseData
from geoh5py.ui_json import InputFile
from simpeg_drivers import DRIVER_MAP

class GravityDriverForward():
    _params_class = GravityForwardParams

class GravityDriver(InversionDriver):
    _params_class = GravityInversionParams
    _validations = validations

    def __init__(self, params):
        super().__init__(params)
    #
    # @classmethod
    # def start(cls, filepath: str | Path, driver_class=None):
    #
    #
    #     ifile = InputFile.read_ui_json(filepath)
    #     with ifile.data["geoh5"].open(mode="r+"):
    #         params = (
    #             GravityForwardParams.build(ifile)
    #             if ifile.data["forward_only"]
    #             else GravityInversionParams.build(ifile)
    #         )
    #         driver = cls(params)
    #         driver.run()
    #
    #     return driver
