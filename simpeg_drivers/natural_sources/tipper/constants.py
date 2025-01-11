# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part simpeg-drivers package.                                        '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from uuid import UUID

from geoh5py.objects.surveys.electromagnetics.tipper import TipperReceivers

import simpeg_drivers
from simpeg_drivers import default_ui_json as base_default_ui_json


inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Tipper Inversion",
    "icon": "surveyztem",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "tipper",
    "forward_only": False,
    "data_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "txz_real_channel": None,
    "txz_real_uncertainty": None,
    "txz_imag_channel": None,
    "txz_imag_uncertainty": None,
    "tyz_real_channel": None,
    "tyz_real_uncertainty": None,
    "tyz_imag_channel": None,
    "tyz_imag_uncertainty": None,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "background_conductivity": 1e-3,
    "starting_model": 1e-3,
    "reference_model": None,
    "lower_bound": None,
    "upper_bound": None,
    "topography_object": None,
    "topography": None,
    "active_model": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "alpha_s": 1.0,
    "length_scale_x": 1.0,
    "length_scale_y": 1.0,
    "length_scale_z": 1.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "y_norm": 2.0,
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
    "sens_wts_threshold": 1.0,
    "every_iteration_bool": True,
    "save_sensitivities": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "max_ram": None,
    "store_sensitivities": "ram",
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "distributed_workers": None,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Tipper Forward",
    "icon": "surveyztem",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "tipper",
    "forward_only": True,
    "data_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "txz_real_channel_bool": True,
    "txz_imag_channel_bool": True,
    "tyz_real_channel_bool": True,
    "tyz_imag_channel_bool": True,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "background_conductivity": 1e-3,
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
    "distributed_workers": None,
}

default_ui_json = {
    "title": "Tipper Inversion",
    "icon": "surveyztem",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "inversion_type": "tipper",
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": "{0b639533-f35b-44d8-92a8-f70ecff3fd26}",
        "value": None,
    },
    "txz_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Txz real",
        "value": False,
    },
    "txz_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Txz real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "txz_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "txz_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "txz_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Txz imaginary",
        "value": False,
    },
    "txz_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Txz imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "txz_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "txz_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "tyz_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Tyz real",
        "value": False,
    },
    "tyz_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Tyz real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "tyz_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "tyz_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "tyz_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Tyz imaginary",
        "value": False,
    },
    "tyz_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Tyz imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "tyz_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "tyz_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "model_type": {
        "choiceList": ["Conductivity (S/m)", "Resistivity (Ohm-m)"],
        "main": True,
        "group": "Mesh and models",
        "label": "Model units",
        "tooltip": "Select the units of the model.",
        "value": "Conductivity (S/m)",
    },
    "starting_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": False,
        "parent": "mesh",
        "label": "Initial",
        "property": None,
        "value": 1e-3,
    },
    "reference_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "main": True,
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Reference",
        "property": None,
        "optional": True,
        "enabled": False,
        "value": 1e-3,
    },
    "background_conductivity": {
        "group": "Mesh and models",
        "main": True,
        "label": "Background",
        "property": None,
        "value": 1e-3,
    },
    "lower_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Lower bound",
        "property": None,
        "optional": True,
        "value": 1e-8,
        "enabled": False,
    },
    "upper_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Upper bound",
        "property": None,
        "optional": True,
        "value": 100.0,
        "enabled": False,
    },
}
default_ui_json = dict(base_default_ui_json, **default_ui_json)
validations = {
    "inversion_type": {
        "required": True,
        "values": ["tipper"],
    },
    "data_object": {"required": True, "types": [str, UUID, TipperReceivers]},
}
app_initializer = {}
