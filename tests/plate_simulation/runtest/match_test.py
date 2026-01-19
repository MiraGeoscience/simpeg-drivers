# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import numpy as np
from geoh5py import Workspace
from geoh5py.groups import PropertyGroup
from geoh5py.objects import Points

from simpeg_drivers.plate_simulation.match.options import PlateMatchOptions
from simpeg_drivers.utils.synthetics.driver import (
    SyntheticsComponents,
)
from simpeg_drivers.utils.synthetics.options import (
    MeshOptions,
    ModelOptions,
    SurveyOptions,
    SyntheticsComponentsOptions,
)
from tests.utils.targets import get_workspace


def generate_example(geoh5: Workspace, n_grid_points: int, refinement: tuple[int]):
    opts = SyntheticsComponentsOptions(
        method="airborne tdem",
        survey=SurveyOptions(
            n_stations=n_grid_points, n_lines=n_grid_points, drape=10.0
        ),
        mesh=MeshOptions(refinement=refinement, padding_distance=400.0),
        model=ModelOptions(background=0.001),
    )
    components = SyntheticsComponents(geoh5, options=opts)
    vals = components.survey.add_data(
        {"observed_data": {"values": np.random.randn(components.survey.n_vertices)}},
    )
    components.property_group = PropertyGroup(components.survey, properties=vals)
    components.queries = Points.create(geoh5, vertices=np.random.randn(1, 3))

    return components


def test_file_parsing(tmp_path: Path):
    """
    Generate a few files and test the
    plate_simulation.match.Options.simulation_files() method.
    """
    filenames = [
        "sim_001.txt",
        "sim_002.txt",
        "sim_010.txt",
        "sim_011.txt",
    ]
    for fname in filenames:
        (tmp_path / fname).touch()

    with get_workspace(tmp_path / f"{__name__}.geoh5") as geoh5:
        components = generate_example(geoh5, n_grid_points=3, refinement=(2,))
        options = PlateMatchOptions(
            geoh5=geoh5,
            survey=components.survey,
            data=components.property_group,
            queries=components.queries,
            topography_object=components.topography,
            simulations=tmp_path,
        )

    sim_files = options.simulation_files
    assert len(sim_files) == 1
    assert sim_files[0].name == f"{__name__}.geoh5"
