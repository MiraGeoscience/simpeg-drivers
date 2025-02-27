# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path
from typing import ClassVar

from geoh5py.ui_json.forms import (
    BoolForm,
    ChoiceForm,
    DataForm,
    FileForm,
    FloatForm,
    GroupForm,
    IntegerForm,
    ObjectForm,
    StringForm,
)
from geoh5py.ui_json.ui_json import BaseUIJson

from simpeg_drivers import assets_path
from simpeg_drivers.uijson import BaseInversionUIJson, SimPEGDriversUIJson


class GravityForwardUIJson(SimPEGDriversUIJson):
    """Gravity Forward UIJson."""

    default_ui_json: ClassVar[Path] = assets_path / "gravity_forward.ui.json"

    inversion_type: str
    forward_only: str
    data_object: ObjectForm
    gz_channel: DataForm
    gz_uncertainty: DataForm
    gx_channel: DataForm
    gx_uncertainty: DataForm
    gy_channel: DataForm
    gy_uncertainty: DataForm
    guv_channel: DataForm
    guv_uncertainty: DataForm
    gxy_channel: DataForm
    gxy_uncertainty: DataForm
    gxx_channel: DataForm
    gxx_uncertainty: DataForm
    gyy_channel: DataForm
    gyy_uncertainty: DataForm
    gzz_channel: DataForm
    gzz_uncertainty: DataForm
    gxz_channel: DataForm
    gxz_uncertainty: DataForm
    gyz_channel: DataForm
    gyz_uncertainty: DataForm
    mesh: ObjectForm
    starting_model: DataForm
    reference_model: DataForm
    lower_bound: DataForm
    upper_bound: DataForm
    topography_object: ObjectForm
    topography: DataForm
    active_model: DataForm
    output_tile_files: bool
    inversion_style: str
    alpha_s: DataForm
    length_scale_x: DataForm
    length_scale_y: DataForm
    length_scale_z: DataForm
    s_norm: DataForm
    x_norm: DataForm
    y_norm: DataForm
    z_norm: DataForm
    gradient_type: ChoiceForm
    max_irls_iterations: IntegerForm
    starting_chi_factor: FloatForm
    beta_tol: FloatForm
    prctile: IntegerForm
    chi_factor: FloatForm
    auto_scale_misfits: BoolForm
    initial_beta_ratio: FloatForm
    initial_beta: FloatForm
    coolingFactor: FloatForm
    coolingRate: IntegerForm
    max_global_iteration: IntegerForm
    max_line_search_iterations: IntegerForm
    max_cg_iterations: IntegerForm
    tol_cg: FloatForm
    f_min_change: FloatForm
    sens_wts_threshold: FloatForm
    every_iteration_bool: BoolForm
    save_sensitivity: BoolForm
    parallelized: BoolForm
    n_cpu: IntegerForm
    tile_spatial: IntegerForm
    store_sensitivities: ChoiceForm
    max_ram: str
    max_chunk_size: IntegerForm
    out_group: GroupForm


class GravityInversionUIJson(SimPEGDriversUIJson):
    default_ui_json: ClassVar[Path] = assets_path / "gravity_inversion.ui.json"
    title: str = "Gravity Inversion"
    inversion_type: str = "gravity"

    gx_channel_bool: bool = False
    gy_channel_bool: bool = False
    gz_channel_bool: bool = True
    gxx_channel_bool: bool = False
    gxy_channel_bool: bool = False
    gxz_channel_bool: bool = False
    gyy_channel_bool: bool = False
    gyz_channel_bool: bool = False
    gzz_channel_bool: bool = False
