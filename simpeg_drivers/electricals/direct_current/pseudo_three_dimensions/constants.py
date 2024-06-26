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
from simpeg_drivers.constants import validations as base_validations

inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Direct Current (DC) 2D Batch Inversion",
    "icon": "PotentialElectrode",
    "inversion_type": "direct current pseudo 3d",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "forward_only": False,
    "topography_object": None,
    "topography": None,
    "data_object": None,
    "line_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": 0.0,
    "gps_receivers_offset": None,
    "potential_channel": None,
    "potential_uncertainty": 1.0,
    "u_cell_size": 25.0,
    "v_cell_size": 25.0,
    "depth_core": 500.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "expansion_factor": 1.1,
    "mesh": None,
    "starting_model": 1e-3,
    "reference_model": 1e-3,
    "lower_bound": None,
    "upper_bound": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "chi_factor": 1.0,
    "initial_beta_ratio": 10.0,
    "initial_beta": None,
    "coolingRate": 2,
    "coolingFactor": 2.0,
    "max_global_iterations": 50,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 30,
    "tol_cg": 1e-4,
    "alpha_s": 1.0,
    "length_scale_x": 1.0,
    "length_scale_z": 1.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "z_norm": 2.0,
    "gradient_type": "total",
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
    "tile_spatial": 1,
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "generate_sweep": False,
    "files_only": False,
    "cleanup": True,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "run_command_boolean": False,
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
    "potential_channel_bool": True,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Direct Current (DC) 2D Batch Forward",
    "icon": "PotentialElectrode",
    "inversion_type": "direct current pseudo 3d",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "forward_only": True,
    "topography_object": None,
    "topography": None,
    "data_object": None,
    "line_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": 0.0,
    "gps_receivers_offset": None,
    "potential_channel_bool": True,
    "u_cell_size": 25.0,
    "v_cell_size": 25.0,
    "depth_core": 500.0,
    "horizontal_padding": 1000.0,
    "vertical_padding": 1000.0,
    "expansion_factor": 1.1,
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
    "files_only": False,
    "cleanup": False,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "run_command": "simpeg_drivers.driver",
    "run_command_boolean": False,
    "conda_environment": "simpeg_drivers",
    "distributed_workers": None,
}

default_ui_json = {
    "title": "Direct Current (DC) 3D Inversion",
    "icon": "PotentialElectrode",
    "inversion_type": "direct current pseudo 3d",
    "line_object": {
        "association": "Cell",
        "dataType": "Referenced",
        "group": "Data",
        "main": True,
        "label": "Line ID",
        "parent": "data_object",
        "value": None,
    },
    "data_object": {
        "main": True,
        "group": "Data",
        "label": "Object",
        "meshType": "{275ecee9-9c24-4378-bf94-65f3c5fbe163}",
        "value": None,
    },
    "potential_channel_bool": True,
    "potential_channel": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Potential (V/I)",
        "parent": "data_object",
        "value": None,
    },
    "potential_uncertainty": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "property": None,
        "value": 1.0,
    },
    "mesh": {
        "group": "Mesh and models",
        "main": True,
        "label": "Mesh",
        "meshType": "{4EA87376-3ECE-438B-BF12-3479733DED46}",
        "optional": True,
        "enabled": False,
        "value": None,
        "visible": True,
    },
    "u_cell_size": {
        "min": 0.0,
        "group": "Mesh and models",
        "main": True,
        "enabled": True,
        "label": "Easting core cell size (m)",
        "value": 25.0,
    },
    "v_cell_size": {
        "min": 0.0,
        "group": "Mesh and models",
        "main": True,
        "enabled": True,
        "label": "Northing core cell size (m)",
        "value": 25.0,
    },
    "depth_core": {
        "min": 0.0,
        "group": "Mesh and models",
        "main": True,
        "enabled": True,
        "label": "Depth of core (m)",
        "value": 500.0,
    },
    "horizontal_padding": {
        "min": 0.0,
        "group": "Mesh and models",
        "main": True,
        "enabled": True,
        "label": "Horizontal padding (m)",
        "value": 1000.0,
    },
    "vertical_padding": {
        "min": 0.0,
        "group": "Mesh and models",
        "main": True,
        "dependencyType": "disabled",
        "label": "Vertical padding (m)",
        "value": 1000.0,
    },
    "expansion_factor": {
        "main": True,
        "group": "Mesh and models",
        "label": "Expansion factor",
        "value": 1.1,
    },
    "starting_model": {
        "association": "Cell",
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": False,
        "parent": "mesh",
        "label": "Initial Conductivity (S/m)",
        "property": None,
        "value": 1e-3,
    },
    "reference_model": {
        "association": "Cell",
        "dataType": "Float",
        "main": True,
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Reference Conductivity (S/m)",
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
    "tile_spatial": 1,
    "files_only": {
        "label": "Generate files only",
        "group": "Python run preferences",
        "main": True,
        "value": False,
    },
    "cleanup": {
        "main": True,
        "group": "Python run preferences",
        "label": "Clean directory",
        "value": True,
    },
}

default_ui_json = dict(base_default_ui_json, **default_ui_json)


################ Validations #################

validations = {
    "inversion_type": {
        "required": True,
        "values": ["direct current pseudo 3d", "direct current 2d"],
    },
    "data_object": {"required": True, "types": [UUID, PotentialElectrode]},
}

validations = dict(base_validations, **validations)

app_initializer = {
    "geoh5": str(assets_path() / "FlinFlon_dcip.geoh5"),
    "data_object": UUID("{6e14de2c-9c2f-4976-84c2-b330d869cb82}"),
    "potential_channel": UUID("{502e7256-aafa-4016-969f-5cc3a4f27315}"),
    "potential_uncertainty": UUID("{62746129-3d82-427e-a84c-78cded00c0bc}"),
    "line_object": UUID("{d400e8f1-8460-4609-b852-b3b93f945770}"),
    "mesh": UUID("{da109284-aa8c-4824-a647-29951109b058}"),
    "starting_model": 1e-1,
    "reference_model": 1e-1,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "z_norm": 2.0,
    "upper_bound": 100.0,
    "lower_bound": 1e-5,
    "max_global_iterations": 25,
    "topography_object": UUID("{ab3c2083-6ea8-4d31-9230-7aad3ec09525}"),
    "topography": UUID("{a603a762-f6cb-4b21-afda-3160e725bf7d}"),
    "z_from_topo": True,
    "receivers_offset_z": 0.0,
    "cleanup": True,
}
