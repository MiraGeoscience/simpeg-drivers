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

from geoh5py.objects import Curve, Grid2D, Points, Surface

import simpeg_drivers


default_ui_json = {
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "icon": "",
    "forward_only": False,
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": [
            "{202C5DB1-A56D-4004-9CAD-BAAFD8899406}",
            "{6A057FDC-B355-11E3-95BE-FD84A7FFCB88}",
            "{F26FEBA3-ADED-494B-B9E9-B2BBCBE298E1}",
            "{48F5054A-1C5C-4CA4-9048-80F36DC60A06}",
            "{b020a277-90e2-4cd7-84d6-612ee3f25051}",
        ],
        "value": None,
        "tooltip": "Select an object containing survey geometry and data for inversion.",
    },
    "z_from_topo": {
        "group": "Data pre-processing",
        "label": "Take z from topography",
        "tooltip": "Sets survey elevation to topography before any offsets are applied.",
        "value": False,
        "verbose": 3,
        "visible": False,
    },
    "receivers_offset_z": {
        "group": "Data pre-processing",
        "label": "Z static offset",
        "optional": True,
        "enabled": False,
        "value": 0.0,
        "verbose": 3,
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
        "value": "",
        "enabled": False,
        "verbose": 3,
        "visible": False,
    },
    "gps_receivers_offset": "",
    "mesh": {
        "group": "Mesh and models",
        "main": True,
        "label": "Mesh",
        "meshType": "{4ea87376-3ece-438b-bf12-3479733ded46}",
        "value": "",
        "optional": True,
        "enabled": False,
        "tooltip": "Select a mesh for the inversion.",
    },
    "starting_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": True,
        "parent": "mesh",
        "label": "Initial",
        "property": "",
        "value": 0.001,
        "tooltip": "Select a model to start the inversion.",
    },
    "reference_model": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "optional": True,
        "enabled": False,
        "parent": "mesh",
        "label": "Reference",
        "property": None,
        "value": 0.0,
    },
    "lower_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Lower bound",
        "property": "",
        "optional": True,
        "value": 1e-08,
        "enabled": False,
        "tooltip": "Minimum value that the model will contain after inversion.",
    },
    "upper_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Upper bound",
        "property": "",
        "optional": True,
        "value": 100.0,
        "enabled": False,
        "tooltip": "Maximum value that the model will contain after inversion.",
    },
    "topography_object": {
        "main": True,
        "group": "Topography",
        "label": "Topography",
        "meshType": [
            "{202c5db1-a56d-4004-9cad-baafd8899406}",
            "{6a057fdc-b355-11e3-95be-fd84a7ffcb88}",
            "{f26feba3-aded-494b-b9e9-b2bbcbe298e1}",
            "{48f5054a-1c5c-4ca4-9048-80f36dc60a06}",
            "{b020a277-90e2-4cd7-84d6-612ee3f25051}",
        ],
        "value": "",
        "optional": True,
        "enabled": True,
        "tooltip": "Select a topography object to define the active cells for inversion.",
    },
    "topography": {
        "association": ["Vertex", "Cell"],
        "dataType": "Float",
        "group": "Topography",
        "main": True,
        "optional": True,
        "enabled": False,
        "label": "Elevation channel",
        "tooltip": "Set elevation from channel.  If not set the topography will be set from the geometry of the selected 'topography' object.",
        "parent": "topography_object",
        "dependency": "topography_object",
        "dependencyType": "enabled",
        "value": "",
        "verbose": 2,
    },
    "active_model": {
        "association": "Cell",
        "dataType": ["Referenced", "Boolean", "Integer"],
        "group": "Topography",
        "main": True,
        "enabled": False,
        "dependency": "topography_object",
        "dependencyType": "disabled",
        "label": "Active model",
        "tooltip": "Provide the active cell boolean model directly if topography not set.",
        "parent": "mesh",
        "value": "",
    },
    "output_tile_files": False,
    "inversion_style": "voxel",
    "alpha_s": {
        "min": 0.0,
        "group": "Regularization",
        "label": "Reference weight",
        "value": 1.0,
        "tooltip": "Constant ratio compared to other weights. Larger values result in models that remain close to the reference model",
        "dependency": "reference_model",
        "dependencyType": "enabled",
        "isValue": True,
        "parent": "mesh",
        "association": "Cell",
        "dataType": "Float",
        "property": "",
        "enabled": False,
    },
    "length_scale_x": {
        "min": 0.0,
        "group": "Regularization",
        "label": "X-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in x biased smoothness",
        "value": 1.0,
        "isValue": True,
        "parent": "mesh",
        "association": "Cell",
        "dataType": "Float",
        "property": "",
        "enabled": True,
    },
    "length_scale_y": {
        "min": 0.0,
        "group": "Regularization",
        "label": "Y-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in y biased smoothness",
        "value": 1.0,
        "isValue": True,
        "parent": "mesh",
        "association": "Cell",
        "dataType": "Float",
        "property": "",
        "enabled": True,
    },
    "length_scale_z": {
        "min": 0.0,
        "group": "Regularization",
        "label": "Z-smoothness weight",
        "tooltip": "Larger values relative to other smoothness weights will result in z biased smoothess",
        "value": 1.0,
        "isValue": True,
        "parent": "mesh",
        "association": "Cell",
        "dataType": "Float",
        "property": "",
        "enabled": True,
    },
    "s_norm": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Sparse/blocky model",
        "label": "Smallness norm",
        "isValue": True,
        "parent": "mesh",
        "property": "",
        "value": 0.0,
        "min": 0.0,
        "max": 2.0,
        "precision": 2,
        "lineEdit": True,
        "enabled": False,
        "dependency": "reference_model",
        "dependencyType": "enabled",
        "tooltip": "Lp-norm used in the smallness term of the objective function.",
    },
    "x_norm": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Sparse/blocky model",
        "label": "X-smoothness norm",
        "isValue": True,
        "parent": "mesh",
        "property": "",
        "value": 2.0,
        "min": 0.0,
        "max": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": True,
        "tooltip": "Lp-norm used in the x-smoothness term of the objective function.",
    },
    "y_norm": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Sparse/blocky model",
        "label": "Y-smoothness norm",
        "isValue": True,
        "parent": "mesh",
        "property": "",
        "value": 2.0,
        "min": 0.0,
        "max": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": True,
        "tooltip": "Lp-norm used in the y-smoothness term of the objective function.",
    },
    "z_norm": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Sparse/blocky model",
        "label": "Z-smoothness norm",
        "isValue": True,
        "parent": "mesh",
        "property": "",
        "value": 2.0,
        "min": 0.0,
        "max": 2.0,
        "precision": 2,
        "lineEdit": False,
        "enabled": True,
        "tooltip": "Lp-norm used in the z-smoothness term of the objective function.",
    },
    "gradient_type": {
        "choiceList": ["total", "components"],
        "group": "Sparse/blocky model",
        "label": "Gradient type",
        "value": "total",
        "verbose": 3,
        "tooltip": "Choose whether the IRLS weights for regularization terms are updated using total or partial gradients.",
    },
    "max_irls_iterations": {
        "min": 0,
        "group": "Sparse/blocky model",
        "label": "Maximum IRLS iterations",
        "tooltip": "Incomplete Re-weighted Least Squares iterations for non-L2 problems",
        "value": 25,
        "enabled": True,
        "verbose": 2,
    },
    "starting_chi_factor": {
        "group": "Sparse/blocky model",
        "label": "IRLS start chi factor",
        "enabled": True,
        "value": 1.0,
        "tooltip": "This chi factor will be used to determine the misfit threshold after which IRLS iterations begin.",
        "verbose": 3,
    },
    "chi_factor": {
        "min": 0.1,
        "max": 20.0,
        "precision": 1,
        "lineEdit": False,
        "group": "Cooling schedule/target",
        "label": "Chi factor",
        "value": 1.0,
        "enabled": True,
        "tooltip": "The global target data misfit value.",
    },
    "auto_scale_misfits": {
        "group": "Cooling schedule/target",
        "label": "Auto-scale misfits",
        "value": True,
        "verbose": 3,
        "visible": True,
        "tooltip": "Whether to auto-scale misfits functions (tile, frequency, joint methods) based on chi-factor.",
    },
    "initial_beta_ratio": {
        "min": 0.0,
        "precision": 2,
        "group": "Cooling schedule/target",
        "optional": True,
        "enabled": True,
        "label": "Initial beta ratio",
        "value": 10.0,
        "verbose": 2,
        "tooltip": "Estimate the trade-off parameter by scaling the ratio between the largest derivatives in the objective function gradients.",
    },
    "initial_beta": {
        "min": 0.0,
        "group": "Cooling schedule/target",
        "optional": True,
        "enabled": False,
        "dependency": "initial_beta_ratio",
        "dependencyType": "disabled",
        "label": "Initial beta",
        "value": 1.0,
        "verbose": 2,
        "tooltip": "Trade-off parameter between data misfit and regularization.",
    },
    "coolingFactor": {
        "group": "Cooling schedule/target",
        "label": "Beta cooling factor",
        "tooltip": "Each beta cooling step will be calculated by dividing the current beta by this factor.",
        "value": 2.0,
        "min": 1.1,
        "max": 100,
        "precision": 1,
        "lineEdit": False,
        "verbose": 2,
    },
    "coolingRate": {
        "group": "Optimization",
        "label": "Iterations per beta",
        "value": 2,
        "min": 1,
        "LineEdit": False,
        "max": 10,
        "precision": 1,
        "verbose": 2,
        "enabled": True,
        "tooltip": "Set the number of iterations per beta value. Use higher values for more non-linear optimization problems.",
    },
    "max_global_iterations": {
        "min": 1,
        "lineEdit": False,
        "group": "Optimization",
        "label": "Maximum iterations",
        "tooltip": "Number of L2 and IRLS iterations combined",
        "value": 50,
        "enabled": True,
    },
    "max_line_search_iterations": {
        "group": "Optimization",
        "label": "Maximum number of line searches",
        "value": 20,
        "min": 1,
        "enabled": True,
        "verbose": 3,
        "tooltip": "Perform an Armijo backtracking linesearch for the provided number of iterations.",
    },
    "max_cg_iterations": {
        "min": 0,
        "group": "Optimization",
        "label": "Maximum CG iterations",
        "value": 30,
        "enabled": True,
        "verbose": 2,
    },
    "tol_cg": {
        "min": 0,
        "group": "Optimization",
        "label": "Conjugate gradient tolerance",
        "value": 0.0001,
        "enabled": True,
        "verbose": 3,
    },
    "f_min_change": {
        "group": "Optimization",
        "label": "Minimum change in objective function",
        "value": 0.01,
        "min": 1e-06,
        "verbose": 3,
        "enabled": True,
        "tooltip": "Minimum decrease in regularization beyond which the IRLS procedure is deemed to have completed.",
    },
    "beta_tol": {
        "group": "Update IRLS directive",
        "label": "Beta tolerance",
        "value": 0.5,
        "min": 0.0001,
        "verbose": 3,
        "visible": False,
    },
    "prctile": {
        "group": "Update IRLS directive",
        "label": "Percentile",
        "value": 95,
        "max": 100,
        "min": 5,
        "verbose": 3,
        "visible": False,
    },
    "coolEps_q": {
        "group": "Update IRLS directive",
        "label": "Cool epsilon q",
        "value": True,
        "verbose": 3,
        "visible": False,
    },
    "coolEpsFact": {
        "group": "Update IRLS directive",
        "label": "Cool epsilon fact",
        "value": 1.2,
        "verbose": 3,
        "visible": False,
    },
    "beta_search": {
        "group": "Update IRLS directive",
        "label": "Perform beta search",
        "value": False,
        "verbose": 3,
        "visible": False,
        "tooltip": "Whether to perform a beta search.",
    },
    "sens_wts_threshold": {
        "group": "Update sensitivity weights directive",
        "tooltip": "Update sensitivity weight threshold",
        "label": "Threshold (%)",
        "value": 1.0,
        "max": 100.0,
        "min": 0.0,
        "precision": 3,
        "enabled": True,
        "verbose": 2,
    },
    "every_iteration_bool": {
        "group": "Update sensitivity weights directive",
        "tooltip": "Update weights at every iteration",
        "label": "Every iteration",
        "value": True,
        "verbose": 2,
        "enabled": True,
    },
    "parallelized": {
        "group": "Compute",
        "label": "Use parallelization",
        "value": True,
        "visible": False,
    },
    "n_cpu": {
        "min": 1,
        "group": "Compute",
        "dependency": "parallelized",
        "dependencyType": "enabled",
        "optional": True,
        "enabled": False,
        "label": "Number of CPUs",
        "value": 1,
        "visible": False,
    },
    "tile_spatial": {
        "group": "Compute",
        "label": "Number of tiles",
        "parent": "data_object",
        "isValue": True,
        "property": "",
        "value": 1,
        "min": 1,
        "max": 1000,
        "verbose": 2,
        "tooltip": "Splits the objective function into spatial tiles for distributed computation using the Dask library.",
    },
    "store_sensitivities": {
        "choiceList": ["disk", "ram"],
        "group": "Compute",
        "label": "Storage device",
        "tooltip": "Use disk on a fast local SSD, and RAM elsewhere",
        "value": "ram",
    },
    "save_sensitivities": {
        "group": "Update sensitivity weights directive",
        "label": "Save sensitivities",
        "tooltip": "Save the summed square row sensitivities to geoh5.",
        "value": False,
    },
    "max_chunk_size": {
        "min": 0,
        "group": "Compute",
        "optional": True,
        "enabled": True,
        "label": "Maximum chunk size (Mb)",
        "value": 128,
        "verbose": 3,
        "visible": False,
        "tooltip": "Limit the chunk size used by Dask for distributed computation.",
    },
    "chunk_by_rows": {
        "group": "Compute",
        "label": "Chunk by rows",
        "value": True,
        "verbose": 3,
        "visible": False,
    },
    "out_group": {
        "label": "SimPEG group",
        "value": "",
        "groupType": "{55ed3daf-c192-4d4b-a439-60fa987fe2b8}",
        "group": "Drag-and-drop options",
        "visible": True,
        "optional": True,
        "enabled": False,
        "tooltip": "Optionally set the SimPEG group to which results will be saved.",
    },
    "generate_sweep": {
        "label": "Generate sweep file",
        "group": "Python run preferences",
        "main": True,
        "value": False,
        "tooltip": "Generates a file for sweeping parameters instead of running the application.",
    },
    "fix_aspect_ratio": True,
    "colorbar": False,
    "ga_group": None,
    "max_ram": None,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "run_command_boolean": None,
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
    "version": simpeg_drivers.__version__,
}

######################## Validations ###########################

validations = {
    "topography_object": {
        "types": [str, UUID, Surface, Points, Grid2D, Curve, type(None)],
    },
    "alpha_s": {"types": [int, float]},
    "length_scale_x": {"types": [int, float]},
    "length_scale_y": {"types": [int, float]},
    "length_scale_z": {"types": [int, float]},
    "norm_s": {"types": [int, float]},
    "norm_x": {"types": [int, float]},
    "norm_y": {"types": [int, float]},
    "norm_z": {"types": [int, float]},
    "distributed_workers": {"types": [str, type(None)]},
    "ga_group": {"types": [str, type(None)]},
    "version": {
        "types": [
            str,
        ]
    },
}
