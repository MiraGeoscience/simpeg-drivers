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

import numpy as np
from geoh5py.groups import UIJsonGroup
from geoh5py.objects import ObjectBase
from geoh5py.shared.utils import fetch_active_workspace
from octree_creation_app.params import OctreeParams

from simpeg_drivers.utils.surveys import station_spacing


def round_nearest(data: np.ndarray, integer: int) -> np.ndarray:
    """Round data to the nearest integer value."""
    return np.round(data / integer) * integer


def auto_pad(survey, factor=2) -> tuple[list[float], list[float]]:
    """
    Estimate horizontal padding as a fraction of the survey extent.

    :param survey: Array of survey locations.
    :param factor: Horizontal padding is the largest survey span (x or y)
        divided by the factor value, ex: factor=2 will pad the survey in
        all horizontal directions by half the largest survey extent.
    :returns horizontal_padding: List of horizontal padding values.
    :returns vertical_padding: List of vertical padding values
    """

    lower = survey[:, :2].min(axis=0)
    upper = survey[:, :2].max(axis=0)
    padding = np.max(upper - lower) / factor

    return padding


def auto_mesh_parameters(
    survey: ObjectBase,
    topography: ObjectBase,
    survey_refinement: list[int] | None = None,
    topography_refinement: list[int] | None = None,
    cell_size_factor: int = 2,
) -> OctreeParams:
    """
    Return a mesh optimized for the provided data extents and spacing.

    :param survey: Survey object.
    :param topography: Topography object.
    :survey_refinement: List specifying how many cells at each octree level
        to refine about the survey locations.
    :topography_refinement: Number of cells to refine in the third octree
        level below the topography.
    :cell_size_factor: Sets the base cell size so that on average, there
        will be N cells between each survey location, where N is the cell
        size factor.
    """

    if survey_refinement is None:
        survey_refinement = [4, 4, 4]

    if topography_refinement is None:
        topography_refinement = [0, 0, 2]

    with fetch_active_workspace(survey.workspace, mode="r+") as workspace:
        spacing = station_spacing(survey.locations) / cell_size_factor
        base_cell_size = round_nearest(spacing, 5)
        padding = auto_pad(survey.locations)
        out_group = UIJsonGroup.create(workspace, name="AutoMesh")
        params_dict = {
            "geoh5": workspace,
            "objects": survey,
            "u_cell_size": base_cell_size,
            "v_cell_size": base_cell_size,
            "w_cell_size": base_cell_size,
            "horizontal_padding": padding,
            "vertical_padding": padding,
            "depth_core": 500.0,
            "diagonal_balance": True,
            "minimum_level": 6,
            "refinements": [
                {
                    "refinement_object": survey,
                    "levels": survey_refinement,
                    "horizon": False,
                },
                {
                    "refinement_object": topography,
                    "levels": topography_refinement,
                    "horizon": True,
                },
            ],
            "out_group":  out_group
        }
        params = OctreeParams(**params_dict)
        dump = params.model_dump()
        ifile = params.input_file
        ifile.data = dump
        options = ifile.stringify(ifile.demote(ifile.ui_json))
        options = bool_to_string(options)
        params.out_group.options = options
        params.out_group.metadata = None
        print(params.out_group.options)

        return params


def bool_to_string(data: dict) -> dict:
    """
    Recurse through dictionary and convert all boolean values to a string 'true' or 'false'.

    :param data: Nested dictionary with boolearn values.
    """
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = bool_to_string(value)
        elif isinstance(value, bool):
            data[key] = str(value).lower()
    return data

