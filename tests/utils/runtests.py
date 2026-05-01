# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoapps_utils.base import Driver, Options
from geoapps_utils.run import run_from_uijson


def run_driver_from_ui_json(params: Options, name: str = "runtest.ui.json") -> Driver:
    """
    Serialize params to a ui.json file and run.

    :param params: Options instance to serialize.
    :param name: Name of the ui.json file to write.
    """
    path = params.geoh5.h5file.parent / name
    params.write_ui_json(path)
    return run_from_uijson(path)
