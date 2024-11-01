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

from geoh5py.objects.surveys.electromagnetics.airborne_fem import AirborneFEMReceivers

import simpeg_drivers
from simpeg_drivers import default_ui_json as base_default_ui_json
from simpeg_drivers.constants import validations as base_validations


inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Frequency-domain EM (FEM) Inversion",
    "icon": "surveyairborneem",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "fem",
    "forward_only": False,
    "data_object": None,
    "z_real_channel": None,
    "z_real_uncertainty": None,
    "z_imag_channel": None,
    "z_imag_uncertainty": None,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
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
    "title": "Frequency-domain EM (FEM) Forward",
    "icon": "surveyairborneem",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "fem",
    "forward_only": True,
    "data_object": None,
    "z_real_channel_bool": True,
    "z_imag_channel_bool": True,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
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
    "title": "Frequency Domain Electromagnetic Inversion",
    "icon": "surveyairborneem",
    "inversion_type": "fem",
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": [
            "{b3a47539-0301-4b27-922e-1dde9d882c60}",  # AirborneFEMReceivers
        ],
        "value": None,
    },
    "z_real_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Z real component",
        "value": False,
    },
    "z_real_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "z-real component",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "z_real_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "z_real_channel",
        "dependencyType": "enabled",
        "value": None,
    },
    "z_imag_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Z imag component",
        "value": False,
    },
    "z_imag_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "z-imag component",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "z_imag_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "dataGroupType": "Multi-element",
        "main": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "z_imag_channel",
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
        "types": [str],
        "required": True,
        "values": ["fem"],
    },
    "data_object": {"types": [str, UUID, AirborneFEMReceivers]},
    "z_real_channel": {"one_of": "data_channel"},
    "z_real_uncertainty": {"one_of": "uncertainty_channel"},
    "z_imag_channel": {"one_of": "data_channel"},
    "z_imag_uncertainty": {"one_of": "uncertainty_channel"},
}
validations = dict(base_validations, **validations)
app_initializer = {}
