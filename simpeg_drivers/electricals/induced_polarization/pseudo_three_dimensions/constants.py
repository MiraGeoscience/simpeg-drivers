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

from uuid import UUID

from geoh5py.objects.surveys.direct_current import PotentialElectrode

import simpeg_drivers
from simpeg_drivers import assets_path
from simpeg_drivers import default_ui_json as base_default_ui_json
from simpeg_drivers.constants import validations as base_validations


inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Induced Polarization (IP) 2D Batch Inversion",
    "icon": "PotentialElectrode",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "induced polarization pseudo 3d",
    "forward_only": False,
    "data_object": None,
    "line_object": None,
    "receivers_radar_drape": None,
    "receivers_offset_z": 0.0,
    "gps_receivers_offset": None,
    "chargeability_channel": None,
    "chargeability_uncertainty": 1.0,
    "u_cell_size": 25.0,
    "v_cell_size": 25.0,
    "depth_core": 500.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "expansion_factor": 1.1,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "conductivity_model": 1e-3,
    "starting_model": 1e-3,
    "reference_model": None,
    "lower_bound": 0.0,
    "upper_bound": None,
    "topography_object": None,
    "topography": None,
    "active_model": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "alpha_s": 1.0,
    "length_scale_x": 1.0,
    "length_scale_z": 1.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "z_norm": 2.0,
    "gradient_type": "total",
    "max_irls_iterations": 25,
    "starting_chi_factor": 1.0,
    "beta_tol": 0.5,
    "prctile": 95,
    "chi_factor": 1.0,
    "auto_scale_misfits": True,
    "initial_beta_ratio": 1e2,
    "initial_beta": None,
    "coolingFactor": 2.0,
    "coolingRate": 2,
    "max_global_iterations": 50,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 30,
    "tol_cg": 1e-4,
    "f_min_change": 0.01,
    "sens_wts_threshold": 0.001,
    "every_iteration_bool": True,
    "save_sensitivities": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "files_only": False,
    "cleanup": True,
    "distributed_workers": None,
    "chargeability_channel_bool": True,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Induced Polarization (IP) 2D Batch Forward",
    "icon": "PotentialElectrode",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "induced polarization pseudo 3d",
    "forward_only": True,
    "data_object": None,
    "line_object": None,
    "receivers_radar_drape": None,
    "receivers_offset_z": 0.0,
    "gps_receivers_offset": None,
    "chargeability_channel_bool": True,
    "u_cell_size": 25.0,
    "v_cell_size": 25.0,
    "depth_core": 500.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "expansion_factor": 1.1,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "conductivity_model": 1e-3,
    "starting_model": 1e-3,
    "topography_object": None,
    "topography": None,
    "active_model": None,
    "output_tile_files": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "files_only": False,
    "cleanup": False,
    "distributed_workers": None,
}

app_initializer = {
    "geoh5": str(assets_path() / "FlinFlon_dcip.geoh5"),
    "data_object": UUID("{6e14de2c-9c2f-4976-84c2-b330d869cb82}"),
    "chargeability_channel": UUID("{162320e6-2b80-4877-9ec1-a8f5b6a13673}"),
    "chargeability_uncertainty": 0.001,
    "line_object": UUID("{d400e8f1-8460-4609-b852-b3b93f945770}"),
    "mesh": UUID("{da109284-aa8c-4824-a647-29951109b058}"),
    "starting_model": 1e-4,
    "conductivity_model": 0.1,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "z_norm": 2.0,
    "upper_bound": 100.0,
    "lower_bound": 1e-5,
    "max_global_iterations": 25,
    "topography_object": UUID("{ab3c2083-6ea8-4d31-9230-7aad3ec09525}"),
    "topography": UUID("{a603a762-f6cb-4b21-afda-3160e725bf7d}"),
    "receivers_offset_z": 0.0,
    "cleanup": True,
}
