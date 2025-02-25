# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from uuid import UUID

from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.ui_json.enforcers import UUIDEnforcer
from geoh5py.ui_json.ui_json import BaseUIJson

import simpeg_drivers


class CoreUIJson(BaseUIJson):
    """
    Core class for ui.json data.
    """

    version: str = simpeg_drivers.__version__
    run_command: str
    conda_environment: str
    forward_only: bool
    data_object: UUID
    mesh: UUID | None
    starting_model: float | UUID
    topography_object: UUID | None
    topography: float | UUID | None
    active_model: UUID | None
    tile_spatial: int
    parallelized: bool
    n_cpu: int | None
    max_chunk_size: int
    save_sensitivities: bool
    out_group: SimPEGGroup | UIJsonGroup | None
    generate_sweep: bool


class BaseInversionUIJson(BaseUIJson):
    """
    Base class for inversion ui.json data.
    """

    reference_model: float | UUID | None
    lower_bound: float | UUID | None
    upper_bound: float | UUID | None

    alpha_s: float | UUID | None
    length_scale_x: float | UUID
    length_scale_y: float | UUID
    length_scale_z: float | UUID

    s_norm: float | UUID | None
    x_norm: float | UUID
    y_norm: float | UUID | None
    z_norm: float | UUID
    gradient_type: str
    max_irls_iterations: int
    starting_chi_factor: float

    chi_factor: float
    auto_scale_misfits: bool
    initial_beta_ratio: float | None
    initial_beta: float | None
    coolingFactor: float

    coolingRate: float
    max_global_iterations: int
    max_line_search_iterations: int
    max_cg_iterations: int
    tol_cg: float
    f_min_change: float

    sens_wts_threshold: float
    every_iteration_bool: bool
    save_sensitivities: str

    beta_tol: float
    prctile: float
    coolEps_q: bool
    coolEpsFact: float
    beta_search: bool

    chunk_by_rows: bool
    output_tile_files: bool
    inversion_style: str
    max_ram: float | None
    ga_group: SimPEGGroup | None
    distributed_workers: int | None
    no_data_value: float | None
