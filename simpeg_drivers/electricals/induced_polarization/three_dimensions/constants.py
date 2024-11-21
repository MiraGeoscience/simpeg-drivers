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

from geoh5py.objects.surveys.direct_current import PotentialElectrode

import simpeg_drivers
from simpeg_drivers import assets_path
from simpeg_drivers import default_ui_json as base_default_ui_json


inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Induced Polarization (IP) 3D Inversion",
    "icon": "PotentialElectrode",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "induced polarization 3d",
    "forward_only": False,
    "data_object": None,
    "z_from_topo": True,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "chargeability_channel": None,
    "chargeability_uncertainty": 1.0,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "conductivity_model": 1e-3,
    "starting_model": 0.0,
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
    "sens_wts_threshold": 0.001,
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
    "chargeability_channel_bool": True,
}

forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Induced Polarization (IP) 3D Forward",
    "icon": "PotentialElectrode",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "induced polarization 3d",
    "forward_only": True,
    "data_object": None,
    "z_from_topo": True,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "chargeability_channel_bool": True,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "conductivity_model": 1e-3,
    "starting_model": None,
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
    "title": "Induced Polarization (IP) 3D Inversion",
    "documentation": "https://mirageoscience-geoapps.readthedocs-hosted.com/en/stable/content/applications/dcip_inversion.html",
    "icon": "PotentialElectrode",
    "inversion_type": "induced polarization 3d",
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": "{275ecee9-9c24-4378-bf94-65f3c5fbe163}",
        "value": None,
    },
    "z_from_topo": {
        "group": "Data",
        "main": True,
        "label": "Surface survey",
        "tooltip": "Uncheck if borehole data is present",
        "value": True,
    },
    "chargeability_channel_bool": True,
    "chargeability_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Chargeability (V/V)",
        "parent": "data_object",
        "value": None,
    },
    "chargeability_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "property": None,
        "value": 1.0,
    },
    "starting_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": False,
        "parent": "mesh",
        "label": "Initial Chargeability (V/V)",
        "property": None,
        "min": 0.0,
        "max": 10000.0,
        "value": 0.0,
    },
    "reference_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "main": True,
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Reference Chargeability (V/V)",
        "property": None,
        "optional": True,
        "enabled": False,
        "value": 0.0,
    },
    "model_type": {
        "choiceList": ["Conductivity (S/m)", "Resistivity (Ohm-m)"],
        "main": True,
        "group": "Mesh and models",
        "label": "Model units",
        "tooltip": "Select the units of the model.",
        "value": "Conductivity (S/m)",
    },
    "conductivity_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": True,
        "parent": "mesh",
        "label": "Conductivity (S/m)",
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
        "label": "Lower bound (V/V)",
        "property": None,
        "optional": True,
        "value": 0,
        "enabled": False,
    },
    "upper_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Upper bound (V/V",
        "property": None,
        "optional": True,
        "value": 100.0,
        "enabled": False,
    },
    "receivers_offset_z": {
        "group": "Data pre-processing",
        "label": "Z static offset",
        "optional": True,
        "enabled": False,
        "value": 0.0,
        "visible": False,
    },
    "receivers_radar_drape": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data pre-processing",
        "label": "Z radar offset",
        "tooltip": "Apply a non-homogeneous offset to survey object from radar channel.",
        "optional": True,
        "parent": "data_object",
        "value": None,
        "enabled": False,
        "visible": False,
    },
}

default_ui_json = dict(base_default_ui_json, **default_ui_json)


################ Validations ##################

validations = {
    "inversion_type": {
        "required": True,
        "values": ["induced polarization 3d"],
    },
    "conductivity_model": {"required": True},
    "data_object": {"required": True, "types": [UUID, PotentialElectrode]},
}

app_initializer = {
    "geoh5": str(assets_path() / "FlinFlon_dcip.geoh5"),
    "data_object": UUID("{6e14de2c-9c2f-4976-84c2-b330d869cb82}"),
    "chargeability_channel": UUID("{162320e6-2b80-4877-9ec1-a8f5b6a13673}"),
    "chargeability_uncertainty": 0.001,
    "mesh": UUID("{da109284-aa8c-4824-a647-29951109b058}"),
    "starting_model": 1e-4,
    "conductivity_model": 0.1,
    "octree_levels_topo": [0, 0, 4, 4],
    "octree_levels_obs": [4, 4, 4, 4],
    "depth_core": 1200.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "y_norm": 2.0,
    "z_norm": 2.0,
    "max_global_iterations": 25,
    "topography_object": UUID("{ab3c2083-6ea8-4d31-9230-7aad3ec09525}"),
    "topography": UUID("{a603a762-f6cb-4b21-afda-3160e725bf7d}"),
    "z_from_topo": True,
    "receivers_offset_z": 0.0,
}
