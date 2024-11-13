# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
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

import simpeg_drivers


defaults = {
    "version": simpeg_drivers.__version__,
    "title": "Gravity Inversion",
    "icon": "surveyairbornegravity",
    "documentation": "https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/en/stable/intro.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,  # Must remain at top of list for notebook app initialization
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "mesh": None,
    "sensitivity_model": None,
    "sensitivity_cutoff": 0.1,
}

default_ui_json = {
    "version": simpeg_drivers.__version__,
    "title": "Gravity Inversion",
    "documentation": "https://geoapps.readthedocs.io/en/stable/content/applications/grav_mag_inversion.html",
    "conda_environment": "simpeg_drivers",
    "run_command": "simpeg_drivers.driver",
    "geoh5": None,
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "mesh": {
        "main": True,
        "group": "Sensitivity",
        "meshType": ["4ea87376-3ece-438b-bf12-3479733ded46"],
        "label": "Mesh",
        "value": None,
    },
    "sensitivity_model": {
        "main": True,
        "group": "Sensitivity",
        "parent": "mesh",
        "association": "Cell",
        "dataType": "Float",
        "label": "Sensitivity",
        "value": None,
    },
    "sensitivity_cutoff": {
        "main": True,
        "group": "Sensitivity",
        "label": "cutoff percentile",
        "tooltip": "Percentile used in cutoff mask.",
        "value": 0.1,
    },
}
