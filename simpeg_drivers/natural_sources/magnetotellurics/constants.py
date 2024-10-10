# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from uuid import UUID

from geoh5py.objects.surveys.electromagnetics.magnetotellurics import MTReceivers

import simpeg_drivers
from simpeg_drivers import assets_path
from simpeg_drivers import default_ui_json as base_default_ui_json
from simpeg_drivers.constants import validations as base_validations


################# defaults ##################

inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Magnetotellurics (MT) Inversion",
    "icon": "surveymagnetotellurics",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "magnetotellurics",
    "forward_only": False,
    "data_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "zxx_real_channel": None,
    "zxx_real_uncertainty": None,
    "zxx_imag_channel": None,
    "zxx_imag_uncertainty": None,
    "zxy_real_channel": None,
    "zxy_real_uncertainty": None,
    "zxy_imag_channel": None,
    "zxy_imag_uncertainty": None,
    "zyx_real_channel": None,
    "zyx_real_uncertainty": None,
    "zyx_imag_channel": None,
    "zyx_imag_uncertainty": None,
    "zyy_real_channel": None,
    "zyy_real_uncertainty": None,
    "zyy_imag_channel": None,
    "zyy_imag_uncertainty": None,
    "mesh": None,
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
    "starting_chi_factor": 2.0,
    "beta_tol": 0.5,
    "prctile": 95,
    "chi_factor": 1.0,
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
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "distributed_workers": None,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Magnetotellurics (MT) Forward",
    "icon": "surveymagnetotellurics",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "magnetotellurics",
    "forward_only": True,
    "data_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "zxx_real_channel_bool": True,
    "zxx_imag_channel_bool": True,
    "zxy_real_channel_bool": True,
    "zxy_imag_channel_bool": True,
    "zyx_real_channel_bool": True,
    "zyx_imag_channel_bool": True,
    "zyy_real_channel_bool": True,
    "zyy_imag_channel_bool": True,
    "mesh": None,
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
    "title": "Magnetotellurics Inversion",
    "icon": "surveymagnetotellurics",
    "inversion_type": "magnetotellurics",
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": "{b99bd6e5-4fe1-45a5-bd2f-75fc31f91b38}",
        "value": None,
    },
    "zxx_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zxx real",
        "value": False,
    },
    "zxx_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zxx real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zxx_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zxx_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zxx_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zxx imaginary",
        "value": False,
    },
    "zxx_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zxx imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zxx_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zxx_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zxy_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zxy real",
        "value": False,
    },
    "zxy_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zxy real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zxy_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zxy_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zxy_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zxy imaginary",
        "value": False,
    },
    "zxy_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zxy imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zxy_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zxy_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zyx_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zyx real",
        "value": False,
    },
    "zyx_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zyx real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zyx_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zyx_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zyx_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zyx imaginary",
        "value": False,
    },
    "zyx_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zyx imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zyx_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zyx_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zyy_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zyy real",
        "value": False,
    },
    "zyy_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zyy real",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zyy_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zyy_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "zyy_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Zyy imaginary",
        "value": False,
    },
    "zyy_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Zyy imaginary",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "zyy_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "zyy_imag_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "starting_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": False,
        "parent": "mesh",
        "label": "Initial conductivity (S/m)",
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
        "label": "Reference conductivity (S/m)",
        "property": None,
        "optional": True,
        "enabled": False,
        "value": 1e-3,
    },
    "background_conductivity": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": True,
        "parent": "mesh",
        "label": "Background conductivity (S/m)",
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
        "label": "Lower bound (S/m)",
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
        "label": "Upper bound (S/m)",
        "property": None,
        "optional": True,
        "value": 100.0,
        "enabled": False,
    },
}

default_ui_json = dict(base_default_ui_json, **default_ui_json)


################ Validations #################
validations = {
    "inversion_type": {
        "types": [str],
        "required": True,
        "values": ["magnetotellurics"],
    },
    "data_object": {"types": [str, UUID, MTReceivers]},
    "zxx_real_channel": {"one_of": "data_channel"},
    "zxx_real_uncertainty": {"one_of": "uncertainty_channel"},
    "zxx_imag_channel": {"one_of": "data_channel"},
    "zxx_imag_uncertainty": {"one_of": "uncertainty_channel"},
    "zxy_real_channel": {"one_of": "data_channel"},
    "zxy_real_uncertainty": {"one_of": "uncertainty_channel"},
    "zxy_imag_channel": {"one_of": "data_channel"},
    "zxy_imag_uncertainty": {"one_of": "uncertainty_channel"},
    "zyx_real_channel": {"one_of": "data_channel"},
    "zyx_real_uncertainty": {"one_of": "uncertainty_channel"},
    "zyx_imag_channel": {"one_of": "data_channel"},
    "zyx_imag_uncertainty": {"one_of": "uncertainty_channel"},
    "zyy_real_channel": {"one_of": "data_channel"},
    "zyy_real_uncertainty": {"one_of": "uncertainty_channel"},
    "zyy_imag_channel": {"one_of": "data_channel"},
    "zyy_imag_uncertainty": {"one_of": "uncertainty_channel"},
}
validations = dict(base_validations, **validations)

app_initializer = {
    "geoh5": str(assets_path() / "FlinFlon_natural_sources.geoh5"),
    "topography_object": UUID("{cfabb8dd-d1ad-4c4e-a87c-7b3dd224c3f5}"),
    "data_object": UUID("{9664afc1-cbda-4955-b936-526ca771f517}"),
    "zxx_real_channel": UUID("{a73159fc-8c1b-411a-b435-12a5dac4a209}"),
    "zxx_real_uncertainty": UUID("{e752e8d8-e8e3-4575-b20c-bc2d37cbd269}"),
    "zxx_imag_channel": UUID("{46271e74-9573-4cd6-8bcb-4c45495fe539}"),
    "zxx_imag_uncertainty": UUID("{73f77c42-ab78-4972-bb69-b16c990bf7dc}"),
    "zxy_real_channel": UUID("{40bdf2a1-237f-49e4-baa8-a7c0785f369a}"),
    "zxy_real_uncertainty": UUID("{8802e943-354f-4ce4-a81f-dde9ef08b8ec}"),
    "zxy_imag_channel": UUID("{1a135542-b2be-4096-9629-a0bc4357970d}"),
    "zxy_imag_uncertainty": UUID("{fac85198-cbd2-4510-bce7-12b4b5fcae2f}"),
    "zyx_real_channel": UUID("{21e6737d-de1a-4af4-9c92-aeeeb6eecf34}"),
    "zyx_real_uncertainty": UUID("{08141050-365c-40aa-bcfb-54841c9492ce}"),
    "zyx_imag_channel": UUID("{f1d2750a-99bf-4876-833b-19b9f46124a4}"),
    "zyx_imag_uncertainty": UUID("{2664535c-295a-4e2a-b403-2a57a821fe08}"),
    "zyy_real_channel": UUID("{9b7f06e9-5bfb-4a5e-ba90-9cec9990d7d5}"),
    "zyy_real_uncertainty": UUID("{61d1a3e9-f7ff-4fd8-bc61-2d1b24b9adc6}"),
    "zyy_imag_channel": UUID("{c9133116-043b-40d9-853d-21f6357f927f}"),
    "zyy_imag_uncertainty": UUID("{11ebb4f3-eacf-4558-b240-b958526dd273}"),
    "mesh": UUID("{1200396b-bc4a-4519-85e1-558c2dcac1dd}"),
    "starting_model": 0.0003,
    "reference_model": 0.0003,
    "background_conductivity": 0.0003,
    "octree_levels_topo": [0, 0, 4, 4],
    "octree_levels_obs": [4, 4, 4, 4],
    "depth_core": 500.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "y_norm": 2.0,
    "z_norm": 2.0,
    "upper_bound": 100.0,
    "lower_bound": 1e-5,
    "max_global_iterations": 50,
}
