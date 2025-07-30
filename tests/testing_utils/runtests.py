# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from pathlib import Path

import numpy as np
from geoapps_utils.modelling.plates import PlateModel, make_plate
from geoapps_utils.utils.locations import grid_layout
from geoh5py import Workspace

from simpeg_drivers.utils.utils import active_from_xyz
from tests.testing_utils.meshes.factory import get_mesh
from tests.testing_utils.surveys.factory import get_survey
from tests.testing_utils.terrain import gaussian, get_topography_surface


plate_model_default = PlateModel(
    strike_length=40.0,
    dip_length=40.0,
    width=40.0,
    origin=(0.0, 0.0, 10.0),
)


def setup_inversion_workspace(
    work_dir,
    plate_model: PlateModel = plate_model_default,
    background=None,
    anomaly=None,
    cell_size=(5.0, 5.0, 5.0),
    center=(0.0, 0.0, 0.0),
    n_electrodes=20,
    n_lines=5,
    refinement=(4, 6),
    x_limits=(-100.0, 100.0),
    y_limits=(-100.0, 100.0),
    padding_distance=100,
    drape_height=5.0,
    inversion_type="other",
    flatten=False,
    geoh5=None,
):
    """
    Creates a workspace populated with objects to simulate/invert a simple model.


    """

    filepath = Path(work_dir) / "inversion_test.ui.geoh5"
    if geoh5 is None:
        if filepath.is_file():
            filepath.unlink()
        geoh5 = Workspace.create(filepath)

    x_limits = (x_limits[0] + center[0], x_limits[1] + center[0])
    y_limits = (y_limits[0] + center[1], y_limits[1] + center[1])

    # Topography
    def topography_generator(x, y):
        return gaussian(x, y, amplitude=50.0, width=100.0)

    topography = get_topography_surface(
        geoh5=geoh5,
        survey_limits=(x_limits[0], x_limits[1], y_limits[0], y_limits[1]),
        topography=0.0 if flatten else topography_generator,
        shift=center[2],
    )

    # Observation points

    # TODO add validation that n_electrodes can't be < 4 once option class created

    survey = get_survey(
        geoh5,
        inversion_type,
        limits=(x_limits[0], x_limits[1], y_limits[0], y_limits[1]),
        station_spacing=n_electrodes,
        line_spacing=n_lines,
        topography=center[2] if flatten else topography_generator,
        drape_height=center[2] + drape_height,
    )

    entity, mesh = get_mesh(
        inversion_type,
        survey=survey,
        topography=topography,
        cell_size=cell_size,
        refinement=refinement,
        padding_distance=padding_distance,
    )
    active = active_from_xyz(entity, topography.vertices, grid_reference="top")

    # Create the Model
    cell_centers = entity.centroids.copy()

    model = make_plate(
        cell_centers, plate_model, background=background, anomaly=anomaly
    )

    if "1d" in inversion_type:
        model = background * np.ones(mesh.nC)
        model[(mesh.cell_centers[:, 2] < 0) & (mesh.cell_centers[:, 2] > -20)] = anomaly

    model[~active] = np.nan
    model = entity.add_data({"model": {"values": model}})
    geoh5.close()
    return geoh5, entity, model, survey, topography
