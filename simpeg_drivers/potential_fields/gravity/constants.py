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

import multiprocessing
from uuid import UUID

from geoh5py.objects import Grid2D, Points, Surface

import simpeg_drivers
from simpeg_drivers import assets_path
from simpeg_drivers import default_ui_json as base_default_ui_json
from simpeg_drivers.constants import validations as base_validations


inversion_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Gravity Inversion",
    "icon": "surveyairbornegravity",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "gravity",
    "forward_only": False,
    "data_object": None,
    "gz_channel": None,
    "gz_uncertainty": 1.0,
    "gx_channel": None,
    "gx_uncertainty": 1.0,
    "gy_channel": None,
    "gy_uncertainty": 1.0,
    "guv_channel": None,
    "guv_uncertainty": 1.0,
    "gxy_channel": None,
    "gxy_uncertainty": 1.0,
    "gxx_channel": None,
    "gxx_uncertainty": 1.0,
    "gyy_channel": None,
    "gyy_uncertainty": 1.0,
    "gzz_channel": None,
    "gzz_uncertainty": 1.0,
    "gxz_channel": None,
    "gxz_uncertainty": 1.0,
    "gyz_channel": None,
    "gyz_uncertainty": 1.0,
    "mesh": None,
    "starting_model": 1e-3,
    "reference_model": None,
    "lower_bound": None,
    "upper_bound": None,
    "topography_object": UUID("{00000000-0000-0000-0000-000000000000}"),
    "topography": None,
    "active_model": None,
    "output_tile_files": False,
    "inversion_style": "voxel",
    "alpha_s": 1.0,
    "length_scale_x": 1.0,
    "length_scale_y": 1.0,
    "length_scale_z": 1.0,
    "s_norm": None,
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
    "coolingRate": 1,
    "max_global_iterations": 50,
    "max_line_search_iterations": 20,
    "max_cg_iterations": 30,
    "tol_cg": 1e-4,
    "f_min_change": 0.01,
    "sens_wts_threshold": 1.0,
    "every_iteration_bool": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "store_sensitivities": "ram",
    "max_ram": None,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "ga_group": None,
    "generate_sweep": False,
    "distributed_workers": None,
}
forward_defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Gravity Forward",
    "icon": "surveyairbornegravity",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "inversion_type": "gravity",
    "forward_only": True,
    "data_object": None,
    "z_from_topo": False,
    "receivers_radar_drape": None,
    "receivers_offset_z": None,
    "gps_receivers_offset": None,
    "gz_channel_bool": True,
    "gx_channel_bool": False,
    "gy_channel_bool": False,
    "guv_channel_bool": False,
    "gxy_channel_bool": False,
    "gxx_channel_bool": False,
    "gyy_channel_bool": False,
    "gzz_channel_bool": False,
    "gxz_channel_bool": False,
    "gyz_channel_bool": False,
    "mesh": None,
    "starting_model": None,
    "topography_object": UUID("{00000000-0000-0000-0000-000000000000}"),
    "topography": None,
    "active_model": None,
    "output_tile_files": False,
    "parallelized": True,
    "n_cpu": None,
    "tile_spatial": 1,
    "max_chunk_size": 128,
    "chunk_by_rows": True,
    "out_group": None,
    "ga_group": None,
    "generate_sweep": False,
    "distributed_workers": None,
}

default_ui_json = {
    "title": "Gravity Inversion",
    "documentation": "https://geoapps.readthedocs.io/en/stable/content/applications/grav_mag_inversion.html",
    "icon": "surveyairbornegravity",
    "inversion_type": "gravity",
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
            "{b54f6be6-0eb5-4a4e-887a-ba9d276f9a83}",
            "{5ffa3816-358d-4cdd-9b7d-e1f7f5543e05}",
        ],
        "value": None,
    },
    "gz_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gz (mGal)",
        "value": False,
    },
    "gz_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gz (mGal)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gz_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gz_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gx_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gx (mGal)",
        "value": False,
    },
    "gx_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gx (mGal)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gx_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gx_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gy_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gy (mGal)",
        "value": False,
    },
    "gy_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gy (mGal)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gy_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gy_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "guv_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Guv (Eo)",
        "value": False,
    },
    "guv_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Guv (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "guv_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "guv_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gxy_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gxy/Gne (Eo)",
        "value": False,
    },
    "gxy_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gxy/Gne (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gxy_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gxy_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gxx_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gxx (Eo)",
        "value": False,
    },
    "gxx_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gxx (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gxx_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gxx_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gyy_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gyy (Eo)",
        "value": False,
    },
    "gyy_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gyy (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gyy_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gyy_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gzz_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gzz (Eo)",
        "value": False,
    },
    "gzz_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gzz (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gzz_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gzz_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gxz_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gxz (Eo)",
        "value": False,
    },
    "gxz_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gxz (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gxz_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gxz_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "gyz_channel_bool": {
        "group": "Data",
        "main": True,
        "label": "Gyz (Eo)",
        "value": False,
    },
    "gyz_channel": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "label": "Gyz (Eo)",
        "parent": "data_object",
        "optional": True,
        "enabled": False,
        "value": None,
    },
    "gyz_uncertainty": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Data",
        "main": True,
        "isValue": True,
        "label": "Uncertainty",
        "parent": "data_object",
        "dependency": "gyz_channel",
        "dependencyType": "enabled",
        "property": None,
        "value": 1.0,
    },
    "coolingRate": {
        "group": "Optimization",
        "label": "Iterations per beta",
        "value": 1,
        "min": 1,
        "LineEdit": False,
        "max": 10,
        "precision": 1,
        "verbose": 2,
        "groupOptional": True,
        "enabled": False,
    },
    "starting_model": {
        "association": ["Cell", "Vertex"],
        "dataType": "Float",
        "group": "Mesh and models",
        "main": True,
        "isValue": True,
        "parent": "mesh",
        "label": "Initial density (g/cc)",
        "property": None,
        "value": 1e-3,
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
        "label": "Reference density (g/cc)",
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
        "label": "Lower bound (g/cc)",
        "property": None,
        "optional": True,
        "value": -10.0,
        "enabled": False,
    },
    "upper_bound": {
        "association": ["Cell", "Vertex"],
        "main": True,
        "dataType": "Float",
        "group": "Mesh and models",
        "isValue": True,
        "parent": "mesh",
        "label": "Upper bound (g/cc)",
        "property": None,
        "optional": True,
        "value": 10.0,
        "enabled": False,
    },
}
default_ui_json = dict(base_default_ui_json, **default_ui_json)
validations = {
    "inversion_type": {
        "required": True,
        "values": ["gravity"],
    },
    "data_object": {"types": [str, UUID, Points, Surface, Grid2D]},
    "gz_channel": {"one_of": "data channel"},
    "gz_uncertainty": {"one_of": "uncertainty channel"},
    "guv_channel": {"one_of": "data channel"},
    "guv_uncertainty": {"one_of": "uncertainty channel"},
    "gxy_channel": {"one_of": "data channel"},
    "gxy_uncertainty": {"one_of": "uncertainty channel"},
    "gxx_channel": {"one_of": "data channel"},
    "gxx_uncertainty": {"one_of": "uncertainty channel"},
    "gyy_channel": {"one_of": "data channel"},
    "gyy_uncertainty": {"one_of": "uncertainty channel"},
    "gzz_channel": {"one_of": "data channel"},
    "gzz_uncertainty": {"one_of": "uncertainty channel"},
    "gxz_channel": {"one_of": "data channel"},
    "gxz_uncertainty": {"one_of": "uncertainty channel"},
    "gyz_channel": {"one_of": "data channel"},
    "gyz_uncertainty": {"one_of": "uncertainty channel"},
    "gx_channel": {"one_of": "data channel"},
    "gx_uncertainty": {"one_of": "uncertainty channel"},
    "gy_channel": {"one_of": "data channel"},
    "gy_uncertainty": {"one_of": "uncertainty channel"},
}
validations = dict(base_validations, **validations)
app_initializer = {
    "geoh5": str(assets_path() / "FlinFlon.geoh5"),
    "monitoring_directory": str((assets_path() / "Temp").resolve()),
    "forward_only": False,
    "data_object": UUID("{538a7eb1-2218-4bec-98cc-0a759aa0ef4f}"),
    "gxx_channel": UUID("{53e59b2b-c2ae-4b77-923b-23e06d874e62}"),
    "gxx_uncertainty": 1.0,
    "gyy_channel": UUID("{51c0acd7-84b8-421f-a66b-fdc15c826a47}"),
    "gyy_uncertainty": 1.0,
    "gzz_channel": UUID("{f450906d-80e2-4c50-ab27-6da5cf0906af}"),
    "gzz_uncertainty": 1.0,
    "gxy_channel": UUID("{9c2afb52-d7b6-4a21-88e9-23bfe9459529}"),
    "gxy_uncertainty": 1.0,
    "gxz_channel": UUID("{55a38ea9-ab20-4944-9fe0-3f77b1f4dcc2}"),
    "gxz_uncertainty": 1.0,
    "gyz_channel": UUID("{3d19bd53-8bb8-4634-aeae-4e3a90e9d19e}"),
    "gyz_uncertainty": 1.0,
    "mesh": UUID("{a8f3b369-10bd-4ca8-8bd6-2d2595bddbdf}"),
    "resolution": 50.0,
    "window_center_x": 314565.0,
    "window_center_y": 6072334.0,
    "window_width": 1000.0,
    "window_height": 1500.0,
    "window_azimuth": 0.0,
    "s_norm": 0.0,
    "x_norm": 2.0,
    "y_norm": 2.0,
    "z_norm": 2.0,
    "starting_model": 1e-3,
    "max_global_iterations": 25,
    "topography_object": UUID("{ab3c2083-6ea8-4d31-9230-7aad3ec09525}"),
    "topography": UUID("{a603a762-f6cb-4b21-afda-3160e725bf7d}"),
    "z_from_topo": True,
    "receivers_offset_z": 60.0,
    "fix_aspect_ratio": True,
    "colorbar": False,
    "n_cpu": int(multiprocessing.cpu_count() / 2),
}
