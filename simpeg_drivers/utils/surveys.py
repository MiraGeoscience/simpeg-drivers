#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import PotentialElectrode


def extract_dcip_survey(
    workspace: Workspace,
    survey: PotentialElectrode,
    lines: np.ndarray,
    line_id: int,
    name: str = "Line",
):
    """
    Returns a survey containing data from a single line.

    :param: workspace: geoh5py workspace containing a valid DCIP survey.
    :param: survey: PotentialElectrode object.
    :param: lines: Line indexer for survey.
    :param: line_id: Index of line to extract data from.
    :param: name: Name prefix to assign to the new survey object (to be
        suffixed with the line number).
    """
    current = survey.current_electrodes

    # Extract line locations and store map into full survey
    survey_locs, survey_loc_map = slice_and_map(survey.vertices, lines == line_id)

    # Use line locations to slice cells and store map into full survey
    func = lambda c: (c[0] in survey_loc_map) & (c[1] in survey_loc_map)
    survey_cells, survey_cell_map = slice_and_map(survey.cells, func)
    survey_cells = [[survey_loc_map[i] for i in c] for c in survey_cells]

    # Use line cells to slice ab_cell_ids
    ab_cell_ids = survey.ab_cell_id.values[list(survey_cell_map)]
    ab_cell_ids = np.array(ab_cell_ids, dtype=int) - 1

    # Use line ab_cell_ids to slice current cells
    current_cells, current_cell_map = slice_and_map(
        current.cells, np.unique(ab_cell_ids)
    )

    # Use line current cells to slice current locs
    current_locs, current_loc_map = slice_and_map(
        current.vertices, np.unique(current_cells.ravel())
    )

    # Remap global ids to local counterparts
    ab_cell_ids = np.array([current_cell_map[i] for i in ab_cell_ids])
    current_cells = [[current_loc_map[i] for i in c] for c in current_cells]

    # Save objects
    line_name = f"{name} {line_id}"
    currents = CurrentElectrode.create(
        workspace,
        name=f"{line_name} (currents)",
        vertices=current_locs,
        cells=np.array(current_cells, dtype=np.int32),
        allow_delete=True,
    )
    currents.add_default_ab_cell_id()

    potentials = PotentialElectrode.create(
        workspace,
        name=line_name,
        vertices=survey_locs,
        allow_delete=True,
    )
    potentials.cells = np.array(survey_cells, dtype=np.int32)

    # Add ab_cell_id as referenced data object
    value_map = {k + 1: str(k + 1) for k in ab_cell_ids}
    value_map.update({0: "Unknown"})
    potentials.add_data(
        {
            "A-B Cell ID": {
                "values": np.array(ab_cell_ids + 1, dtype=np.int32),
                "association": "CELL",
                "entity_type": {
                    "primitive_type": "REFERENCED",
                    "value_map": value_map,
                },
            },
            "Global Map": {
                "values": np.array(list(survey_cell_map), dtype=np.int32),
                "association": "CELL",
                "entity_type": {
                    "primitive_type": "REFERENCED",
                    "value_map": {k: str(k) for k in survey_cell_map},
                },
            },
        }
    )

    # Attach current and potential objects and copy data slice into line survey
    potentials.current_electrodes = currents
    for c in survey.children:
        if isinstance(c, FloatData) and "Pseudo" not in c.name:
            potentials.add_data({c.name: {"values": c.values[list(survey_cell_map)]}})

    return potentials