# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from geoh5py.ui_json.forms import (
    BoolForm,
    FloatForm,
    GroupForm,
    IntegerForm,
    StringForm,
)
from geoh5py.ui_json.ui_json import BaseUIJson


class PlateSimulationUIJson(BaseUIJson):
    simulation: GroupForm
    name: StringForm
    background: FloatForm
    overburden: FloatForm
    thickness: FloatForm
    number: IntegerForm
    spacing: FloatForm
    plate: FloatForm
    width: FloatForm
    strike_length: FloatForm
    dip_length: FloatForm
    dip: FloatForm
    dip_direction: FloatForm
    relative_locations: BoolForm
    easting: FloatForm
    northing: FloatForm
    elevation: FloatForm
    reference_surface: StringForm
    reference_type: StringForm
    generate_sweep: BoolForm
    u_cell_size: FloatForm
    v_cell_size: FloatForm
    w_cell_size: FloatForm
    depth_core: FloatForm
    max_distance: FloatForm
    padding_distance: FloatForm
    diagonal_balance: BoolForm
    minimum_level: IntegerForm
    export_model: BoolForm
    out_group: GroupForm
