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
from geoh5py.objects import ObjectBase
from geoh5py.shared.utils import fetch_active_workspace
from octree_creation_app.params import OctreeParams

from simpeg_drivers.utils.surveys import station_spacing


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
    max_dim = np.max(upper - lower)
    horizontal_padding = np.max([xrange, yrange]) / factor

    return [horizontal_padding] * 4, [200.0] * 2


def auto_mesh_parameters(
    survey: ObjectBase,
    topography: ObjectBase,
    survey_refinement: list[int] | None = None,
    topography_refinement: int = 2,
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

    with fetch_active_workspace(survey.workspace, mode="r+") as workspace:
        spacing = station_spacing(survey.locations) / cell_size_factor
        base_cell_size = np.round(spacing)
        horizontal_padding, vertical_padding = auto_pad(survey.locations)

        params_dict = {
            "geoh5": workspace,
            "objects": survey,
            "u_cell_size": base_cell_size,
            "v_cell_size": base_cell_size,
            "w_cell_size": base_cell_size,
            "horizontal_padding": horizontal_padding,
            "vertical_padding": vertical_padding,
            "depth_core": 500,
            "diagonal_balance": True,
            "Refinement A object": survey,
            "Refinement A levels": survey_refinement,
            "Refinement A horizon": False,
            "Refinement B object": topography,
            "Refinement B levels": [0, 0, topography_refinement],
            "Refinement B horizon": True,
            "minimum_level": 8,
        }

        return OctreeParams(**params_dict)
