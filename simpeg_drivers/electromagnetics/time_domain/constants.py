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

from geoh5py.objects import AirborneTEMReceivers, LargeLoopGroundTEMReceivers

import simpeg_drivers
from simpeg_drivers import default_ui_json as base_default_ui_json
from simpeg_drivers.constants import validations as base_validations

inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Time-domain EM (TEM) Inversion",
    "icon": "surveyairborneem",
    "inversion_type": "tdem",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "forward_only": False,
    "topography_object": None,
    "topography": None,
    "data_object": None,
    "data_units": "dB/dt (T/s)",
    "z_channel": None,
    "z_uncertainty": None,
    "x_channel": None,
    "x_uncertainty": None,
    "y_channel": None,
    "y_uncertainty": None,
    "mesh": None,
    "starting_model": 1e-3,
    "reference_model": 1e-3,
    "lower_bound": None,
    "upper_bound": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "length_scale_x": 1.0,
    "length_scale_y": 1.0,
    "length_scale_z": 1.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "y_norm": 2.0,
    "z_norm": 2.0,
    "gradient_type": "total",
    "chi_factor": 1.0,
    "initial_beta_ratio": 1e2,
    "initial_beta": None,
    "coolingRate": 4,
    "coolingFactor": 2.0,
    "max_global_iterations": 50,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 50,
    "tol_cg": 1e-4,
    "alpha_s": 0.0,
    "max_irls_iterations": 25,
    "starting_chi_factor": None,
    "f_min_change": 1e-4,
    "beta_tol": 0.5,
    "prctile": 95,
    "coolEps_q": True,
    "coolEpsFact": 1.2,
    "beta_search": False,
    "sens_wts_threshold": 1.0,
    "every_iteration_bool": True,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Time-domain EM (TEM) Forward",
    "icon": "surveyairborneem",
    "inversion_type": "tdem",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "forward_only": True,
    "topography_object": None,
    "topography": None,
    "data_object": None,
    "data_units": "dB/dt (T/s)",
    "z_channel_bool": True,
    "x_channel_bool": True,
    "y_channel_bool": True,
    "mesh": None,
    "starting_model": 1e-3,
    "output_tile_files": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
}
default_ui_json = {
    "title": "Time Domain Electromagnetic Inversion",
    "icon": "surveyairborneem",
    "inversion_type": "tdem",
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": [
            "{19730589-fd28-4649-9de0-ad47249d9aba}",
            "{deebe11a-b57b-4a03-99d6-8f27b25eb2a8}",
        ],
        "value": None,
    },
    "data_units": {
        "choiceList": ["dB/dt (T/s)", "B (T)", "H (A/m)"],
        "group": "Data",
        "main": True,
        "label": "Data type",
        "tooltip": "Set the units of the data.",
        "value": "dB/dt (T/s)",
    },
    "z_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Z component",
        "value": False,
    },
    "z_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "z-component",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "z_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "z_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "x_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "X component",
        "value": False,
    },
    "x_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "x-component",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "x_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "x_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "y_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Y component",
        "value": False,
    },
    "y_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "y-component",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "y_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "y_channel",
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
        "value": 1e-3,
    },
    "lower_bound": {
        "association": "Cell",
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
        "association": "Cell",
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
    "store_sensitivities": {
        "choiceList": ["ram"],
        "group": "Compute",
        "label": "Storage device",
        "tooltip": "Only RAM storage available for now.",
        "value": "ram",
    },
}
default_ui_json = dict(base_default_ui_json, **default_ui_json)
validations = {
    "inversion_type": {
        "types": [str],
        "required": True,
        "values": ["tdem"],
    },
    "data_object": {
        "types": [str, UUID, AirborneTEMReceivers, LargeLoopGroundTEMReceivers]
    },
    "z_channel": {"one_of": "data_channel"},
    "z_uncertainty": {"one_of": "uncertainty_channel"},
    "x_channel": {"one_of": "data_channel"},
    "x_uncertainty": {"one_of": "uncertainty_channel"},
    "y_channel": {"one_of": "data_channel"},
    "y_uncertainty": {"one_of": "uncertainty_channel"},
}
validations = dict(base_validations, **validations)
app_initializer = {}
