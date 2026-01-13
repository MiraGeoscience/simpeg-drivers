# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoh5py.ui_json.forms import DataForm, FloatForm, ObjectForm, StringForm
from geoh5py.ui_json.ui_json import BaseUIJson
from pydantic import ConfigDict


class PlateMatchUIJson(BaseUIJson):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    survey: ObjectForm
    data: DataForm
    queries: ObjectForm
    strike_angles: DataForm
    max_distance: FloatForm
    topography_object: ObjectForm
    topography: DataForm
    simulations: StringForm
