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

from geoh5py import Workspace

from simpeg_drivers.utils.testing_utils.meshes.factory import get_mesh
from simpeg_drivers.utils.testing_utils.models import get_model
from simpeg_drivers.utils.testing_utils.options import SyntheticDataInversionOptions
from simpeg_drivers.utils.testing_utils.surveys.factory import get_survey
from simpeg_drivers.utils.testing_utils.terrain import get_topography_surface
from simpeg_drivers.utils.utils import active_from_xyz


def setup_inversion_workspace(
    work_dir: Path,
    method: str,
    options: SyntheticDataInversionOptions,
    geoh5=None,
):
    """
    Creates a workspace populated with objects simulations and subsequent inversion.

    :param work_dir: Directory to save the workspace.
    :param method: Geophysical method descriptor used to modify object creation.
    :param options: Options for the generation of objects in the workspace.
    """

    filepath = Path(work_dir) / "inversion_test.ui.geoh5"
    if geoh5 is None:
        if filepath.is_file():
            filepath.unlink()
        geoh5 = Workspace.create(filepath)

    topography = get_topography_surface(
        geoh5=geoh5,
        options=options.survey,
    )

    survey = get_survey(
        geoh5=geoh5,
        method=method,
        options=options.survey,
    )
    # TODO add validation that n_electrodes can't be < 4 once option class created

    entity, mesh = get_mesh(
        method,
        survey=survey,
        topography=topography,
        options=options.mesh,
    )

    active = active_from_xyz(entity, topography.vertices, grid_reference="top")

    # Model

    model = get_model(
        method=method,
        mesh=entity,
        active=active,
        options=options.model,
    )

    geoh5.close()

    return geoh5, entity, model, survey, topography
