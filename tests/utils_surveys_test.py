# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Points

from simpeg_drivers.utils.surveys import counter_clockwise_sort, station_spacing


def create_test_survey(
    n_lines: int = 10,
    line_length: float = 2000.0,
    spacing: float = 20.0,
    jitter: float = 0.2,
):
    """
    Create a set of points on a pseudo-random survey grid.

    :param n_lines: Number of survey lines
    :param line_length: Length in meters of the each survey line
    :param spacing: Station spacing along each line before jitter.
    :param jitter: Station location jitter as a fraction of the station spacing.
    """

    eastings = np.arange(0, 1 + line_length, spacing)
    northings = np.arange(0, 1 + line_length / 2, line_length / (2 * n_lines))

    rng = np.random.default_rng()
    stdev = spacing * jitter / 4

    survey = []
    for i in range(n_lines):
        jittered_eastings = [rng.normal(k, stdev) for k in eastings]
        jittered_northings = [
            rng.normal(k, stdev / 2) for k in np.ones_like(eastings) * northings[i]
        ]
        survey.append(
            np.c_[
                jittered_eastings, jittered_northings, np.zeros_like(jittered_eastings)
            ]
        )

    return np.vstack(survey)


def test_station_spacing(tmp_path):
    survey = create_test_survey(line_length=5000, n_lines=20, spacing=10, jitter=0.1)

    ws = Workspace(tmp_path / "test.geoh5")
    _ = Points.create(ws, name="survey_jitter_0.5", vertices=survey)

    median_spacing = station_spacing(survey, "median")
    mean_spacing = station_spacing(survey, "mean")
    min_spacing = station_spacing(survey, "min")
    max_spacing = station_spacing(survey, "max")

    assert np.isclose(median_spacing, 10, atol=2)
    assert np.isclose(mean_spacing, 10, atol=2)
    assert np.isclose(min_spacing, 10, atol=2)
    assert np.isclose(max_spacing, 10, atol=2)


def test_counterclockwise_sort():
    vertices = np.array(
        [[0, 0], [0.25, 1.5], [0.0, 2.0], [0.5, 1], [1.5, 0], [0.2, 0.2]]
    )
    segments = np.c_[np.arange(len(vertices)), np.arange(1, len(vertices) + 1)]
    segments[-1, 1] = 0

    ccw_sorted = counter_clockwise_sort(segments, vertices)

    np.testing.assert_equal(ccw_sorted[0, :], [0, 5])
