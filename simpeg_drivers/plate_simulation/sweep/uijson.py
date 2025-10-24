# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoh5py.ui_json.forms import FloatForm, GroupForm, IntegerForm, StringForm
from geoh5py.ui_json.ui_json import BaseUIJson
from pydantic import ConfigDict


class PlateSweepUIJson(BaseUIJson):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    template: GroupForm
    background_start: FloatForm
    background_stop: FloatForm
    background_count: IntegerForm
    overburden_start: FloatForm
    overburden_stop: FloatForm
    overburden_count: IntegerForm
    thickness_start: FloatForm
    thickness_stop: FloatForm
    thickness_count: IntegerForm
    plate_start: FloatForm
    plate_stop: FloatForm
    plate_count: IntegerForm
    width_start: FloatForm
    width_stop: FloatForm
    width_count: IntegerForm
    strike_length_start: FloatForm
    strike_length_stop: FloatForm
    strike_length_count: IntegerForm
    dip_length_start: FloatForm
    dip_length_stop: FloatForm
    dip_length_count: IntegerForm
    dip_start: FloatForm
    dip_stop: FloatForm
    dip_count: IntegerForm
    out_group: GroupForm | None
    workdir: StringForm | None
