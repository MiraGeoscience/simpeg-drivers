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

import simpeg_drivers
from simpeg_drivers.constants import validations as base_validations
from simpeg_drivers.joint.constants import default_ui_json as joint_default_ui_json


################# defaults ##################

inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "SimPEG Joint Surveys Inversion",
    "icon": "",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "joint surveys",
    "forward_only": False,
    "group_a": None,
    "group_a_multiplier": 1.0,
    "group_b": None,
    "group_b_multiplier": 1.0,
    "group_c": None,
    "group_c_multiplier": 1.0,
    "mesh": None,
    "model_type": "Conductivity (S/m)",
    "starting_model": None,
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
    "coolingRate": 1,
    "max_global_iterations": 50,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 30,
    "tol_cg": 1e-4,
    "f_min_change": 0.01,
    "sens_wts_threshold": 0.001,
    "every_iteration_bool": True,
    "parallelized": True,
    "n_cpu": None,
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "distributed_workers": None,
}

default_ui_json = {
    "title": "SimPEG Joint Surveys Inversion",
    "inversion_type": "joint surveys",
    "model_type": {
        "choiceList": ["Conductivity (S/m)", "Resistivity (Ohm-m)"],
        "main": True,
        "group": "Mesh and Models",
        "label": "Model units",
        "tooltip": "Select the units of the model.",
        "value": "Conductivity (S/m)",
    },
    "starting_model": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Mesh and Models",
        "main": True,
        "isValue": False,
        "parent": "mesh",
        "label": "Initial model",
        "property": None,
        "optional": True,
        "enabled": False,
        "value": 1e-4,
    },
    "lower_bound": {
        "association": "Cell",
        "main": True,
        "dataType": "Float",
        "group": "Mesh and Models",
        "isValue": False,
        "parent": "mesh",
        "label": "Lower bound)",
        "property": None,
        "optional": True,
        "value": -10.0,
        "enabled": False,
    },
    "upper_bound": {
        "association": "Cell",
        "main": True,
        "dataType": "Float",
        "group": "Mesh and Models",
        "isValue": False,
        "parent": "mesh",
        "label": "Upper bound",
        "property": None,
        "optional": True,
        "value": 10.0,
        "enabled": False,
    },
    "reference_model": {
        "association": "Cell",
        "main": True,
        "dataType": "Float",
        "group": "Mesh and Models",
        "isValue": False,
        "parent": "mesh",
        "label": "Reference",
        "property": None,
        "optional": True,
        "value": 1e-4,
        "enabled": False,
    },
}
default_ui_json = dict(joint_default_ui_json, **default_ui_json)
validations = {
    "inversion_type": {
        "required": True,
        "values": ["joint surveys"],
    },
}

validations = dict(base_validations, **validations)
app_initializer = {}
