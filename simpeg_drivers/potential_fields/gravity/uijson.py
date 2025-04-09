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

from geoh5py.ui_json.annotations import Deprecated
from geoh5py.ui_json.forms import (
    BoolForm,
    ChoiceForm,
    DataForm,
    FloatForm,
    GroupForm,
    IntegerForm,
    ObjectForm,
)
from pydantic import AliasChoices, Field

from simpeg_drivers import assets_path
from simpeg_drivers.uijson import SimPEGDriversUIJson


class GravityForwardUIJson(SimPEGDriversUIJson):
    """Gravity Forward UIJson."""

    default_ui_json: ClassVar[Path] = assets_path() / "uijson/gravity_forward.ui.json"

    inversion_type: str
    forward_only: bool
    data_object: ObjectForm
    gz_channel_bool: BoolForm
    gx_channel_bool: BoolForm
    gy_channel_bool: BoolForm
    guv_channel_bool: BoolForm
    gxy_channel_bool: BoolForm
    gxx_channel_bool: BoolForm
    gyy_channel_bool: BoolForm
    gzz_channel_bool: BoolForm
    gxz_channel_bool: BoolForm
    gyz_channel_bool: BoolForm
    mesh: ObjectForm
    starting_model: DataForm
    topography_object: ObjectForm
    topography: DataForm
    active_model: DataForm
    save_sensitivities: BoolForm
    parallelized: BoolForm
    tile_spatial: DataForm
    max_chunk_size: IntegerForm
    out_group: GroupForm
    generate_sweep: BoolForm
    distributed_workers: str
    z_from_topo: Deprecated | None = None
    receivers_radar_drape: Deprecated | None = None
    receivers_offset_z: Deprecated | None = None
    gps_receivers_offset: Deprecated | None = None
    output_tile_files: Deprecated | None = None
    chunk_by_rows: Deprecated | None = None
    parallelized: Deprecated | None = None
    n_cpu: Deprecated | None = None
    ga_group: Deprecated | None = None


class GravityInversionUIJson(SimPEGDriversUIJson):
    """Gravity Inversion UIJson."""

    default_ui_json: ClassVar[Path] = assets_path() / "uijson/gravity_inversion.ui.json"

    inversion_type: str
    forward_only: bool
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
    alpha_s: DataForm
    length_scale_x: DataForm
    length_scale_y: DataForm
    length_scale_z: DataForm
    gradient_rotation: DataForm
    s_norm: DataForm
    x_norm: DataForm
    y_norm: DataForm
    z_norm: DataForm
    gradient_type: ChoiceForm
    max_irls_iterations: IntegerForm
    starting_chi_factor: FloatForm
    beta_tol: FloatForm
    percentile: IntegerForm = Field(
        validation_alias=AliasChoices("percentile", "prctile")
    )
    chi_factor: FloatForm
    auto_scale_misfits: BoolForm
    initial_beta_ratio: FloatForm
    initial_beta: FloatForm
    cooling_factor: FloatForm = Field(
        validation_alias=AliasChoices("cooling_factor", "coolingFactor")
    )
    cooling_rate: IntegerForm = Field(
        validation_alias=AliasChoices("cooling_rate", "coolingRate")
    )
    epsilon_cooling_factor: float = Field(
        validation_alias=AliasChoices("epsilon_cooling_factor", "coolEpsFact")
    )
    max_global_iterations: IntegerForm
    max_line_search_iterations: IntegerForm
    max_cg_iterations: IntegerForm
    tol_cg: FloatForm
    f_min_change: FloatForm
    sens_wts_threshold: FloatForm
    every_iteration_bool: BoolForm
    save_sensitivities: BoolForm
    n_cpu: IntegerForm
    tile_spatial: DataForm
    store_sensitivities: ChoiceForm
    max_chunk_size: IntegerForm

    out_group: GroupForm
    generate_sweep: BoolForm
    distributed_workers: str
    gradient_type: Deprecated | None = None
    output_tile_files: Deprecated | None = None
    inversion_style: Deprecated | None = None
    max_ram: Deprecated | None = None
    chunk_by_rows: Deprecated | None = None
    parallelized: Deprecated | None = None
    ga_group: Deprecated | None = None
