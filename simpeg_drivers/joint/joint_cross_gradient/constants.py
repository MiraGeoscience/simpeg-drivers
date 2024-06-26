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

from simpeg_drivers.constants import validations as base_validations
from simpeg_drivers.joint.constants import default_ui_json as joint_default_ui_json

inversion_defaults = {
    "title": "SimPEG Joint Cross Gradient Inversion",
    "inversion_type": "joint cross gradient",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "forward_only": False,
    "topography_object": None,
    "topography": None,
    "group_a": None,
    "group_a_multiplier": 1.0,
    "group_b": None,
    "group_b_multiplier": 1.0,
    "cross_gradient_weight_a_b": 1e6,
    "group_c": None,
    "group_c_multiplier": 1.0,
    "cross_gradient_weight_c_a": 1e6,
    "cross_gradient_weight_c_b": 1e6,
    "mesh": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "chi_factor": 1.0,
    "initial_beta_ratio": 10.0,
    "initial_beta": None,
    "coolingRate": 1,
    "coolingFactor": 2.0,
    "max_global_iterations": 100,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 30,
    "tol_cg": 1e-4,
    "alpha_s": None,
    "length_scale_x": None,
    "length_scale_y": None,
    "length_scale_z": None,
    "s_norm": None,
    "x_norm": None,
    "y_norm": None,
    "z_norm": None,
    "gradient_type": None,
    "max_irls_iterations": 25,
    "starting_chi_factor": None,
    "f_min_change": 1e-4,
    "beta_tol": 0.5,
    "prctile": 95,
    "coolEps_q": True,
    "coolEpsFact": 1.2,
    "beta_search": False,
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
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
}
default_ui_json = {
    "title": "SimPEG Joint Cross Gradient Inversion",
    "inversion_type": "joint surveys",
    "cross_gradient_weight_a_b": {
        "min": 0.0,
        "group": "Joint",
        "label": "A x B Coupling Scale",
        "value": 1.0,
        "main": True,
        "lineEdit": False,
        "tooltip": "Weight applied to the cross gradient regularizations (1: equal weight with the standard Smallness and Smoothness terms.)",
    },
    "cross_gradient_weight_c_a": {
        "min": 0.0,
        "group": "Joint",
        "label": "A x C Coupling Scale",
        "value": 1.0,
        "main": True,
        "lineEdit": False,
        "dependency": "group_c",
        "dependencyType": "enabled",
        "tooltip": "Weight applied to the cross gradient regularizations (1: equal weight with the standard Smallness and Smoothness terms.)",
    },
    "cross_gradient_weight_c_b": {
        "min": 0.0,
        "group": "Joint",
        "label": "B x C Coupling Scale",
        "value": 1.0,
        "main": True,
        "lineEdit": False,
        "dependency": "group_c",
        "dependencyType": "enabled",
        "tooltip": "Weight applied to the cross gradient regularizations (1: equal weight with the standard Smallness and Smoothness terms.)",
    },
    "alpha_s": {
        "min": 0.0,
        "group": "Regularization",
        "groupOptional": True,
        "label": "Smallness weight",
        "value": 1.0,
        "tooltip": "Constant ratio compared to other weights. Larger values result in models that remain close to the reference model",
        "enabled": False,
    },
    "length_scale_x": {
        "min": 0.0,
        "group": "Regularization",
        "label": "X-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in x biased smoothness",
        "value": 1.0,
        "enabled": False,
    },
    "length_scale_y": {
        "min": 0.0,
        "group": "Regularization",
        "label": "Y-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in y biased smoothness",
        "value": 1.0,
        "enabled": False,
    },
    "length_scale_z": {
        "min": 0.0,
        "group": "Regularization",
        "label": "Z-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in z biased smoothess",
        "value": 1.0,
        "enabled": False,
    },
    "s_norm": {
        "min": 0.0,
        "max": 2.0,
        "group": "Regularization",
        "label": "Smallness norm",
        "value": 0.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": False,
    },
    "x_norm": {
        "min": 0.0,
        "max": 2.0,
        "group": "Regularization",
        "label": "X-smoothness norm",
        "value": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": False,
    },
    "y_norm": {
        "min": 0.0,
        "max": 2.0,
        "group": "Regularization",
        "label": "Y-smoothness norm",
        "value": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": False,
    },
    "z_norm": {
        "min": 0.0,
        "max": 2.0,
        "group": "Regularization",
        "label": "Z-smoothness norm",
        "value": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": False,
    },
    "gradient_type": {
        "choiceList": ["total", "components"],
        "group": "Regularization",
        "label": "Gradient type",
        "value": "total",
        "verbose": 3,
        "enabled": False,
    },
}
default_ui_json = dict(joint_default_ui_json, **default_ui_json)
validations = {
    "inversion_type": {
        "required": True,
        "values": ["joint cross gradient"],
    },
}
validations = dict(base_validations, **validations)
app_initializer = {}
