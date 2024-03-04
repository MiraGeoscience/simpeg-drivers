#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.
#
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from discretize import TensorMesh, TreeMesh
from discretize.utils import mesh_utils
from geoh5py import Workspace
from geoh5py.groups import Group
from geoh5py.objects import DrapeModel, LargeLoopGroundEMSurvey, Octree
from geoh5py.shared import INTEGER_NDV
from pydantic import BaseModel, ConfigDict
from scipy.spatial import cKDTree
from SimPEG.electromagnetics.frequency_domain.sources import (
    LineCurrent as FEMLineCurrent,
)
from SimPEG.electromagnetics.time_domain.sources import LineCurrent as TEMLineCurrent
from SimPEG.survey import BaseSurvey

from simpeg_drivers.utils.surveys import (
    DistanceMapper,
    compute_alongline_distance,
    get_intersecting_cells,
    get_unique_locations,
)

if TYPE_CHECKING:
    from simpeg_drivers.components import InversionData


def insert_cells_by_locations(
    nested_mesh: TreeMesh,
    base_mesh: TreeMesh,
    locations: np.ndarray,
    padding_cells: int = 8,
    minimum_level: int = 3,
    finalize: bool = True,
):
    """
    Create a nested mesh with the same discretization as the base mesh
    within a padded region around locations.

    :param nested_mesh: Input nested TreeMesh object.
    :param base_mesh: Input global TreeMesh object.
    :param locations: Array of coordinates for the local survey shape(*, 3).
    :param padding_cells: Number of cells in each concentric shell around the locations.
    :param minimum_level: Minimum octree level to preserve in the padding_cells region.
    :param finalize: Return a finalized local treemesh.

    :return nested_mesh: Nested mesh with the same discretization as the base mesh.
    """
    base_cell = np.min([base_mesh.h[0][0], base_mesh.h[1][0]])
    tree = cKDTree(locations[:, :2])
    rad, _ = tree.query(base_mesh.gridCC[:, :2])

    pad_distance = 0.0
    for ii in range(minimum_level):
        pad_distance += base_cell * 2**ii * padding_cells

    indices = np.where(rad < pad_distance)[0]
    levels = base_mesh.cell_levels_by_index(indices)
    levels[levels > (base_mesh.max_level - ii)] = base_mesh.max_level - ii
    nested_mesh.insert_cells(
        base_mesh.gridCC[indices, :],
        levels,
        finalize=False,
    )

    if finalize:
        nested_mesh.finalize()

    return nested_mesh


def create_nested_mesh(
    survey: BaseSurvey,
    base_mesh: TreeMesh,
    padding_cells: int = 8,
    minimum_level: int = 3,
    finalize: bool = True,
):
    """
    Create a nested mesh with the same extent as the input global mesh.
    Refinement levels are preserved only around the input locations (local survey).

    :param base_mesh: Input global TreeMesh object.
    :param padding_cells: Number of cells in each concentric shell.
    :param minimum_level: Minimum octree level to preserve everywhere outside the local survey area.
    :param finalize: Return a finalized local treemesh.

    :return nested_mesh: Nested mesh with the same discretization as the base mesh.
    """
    locations = get_unique_locations(survey)
    nested_mesh = TreeMesh(
        [base_mesh.h[0], base_mesh.h[1], base_mesh.h[2]], x0=base_mesh.x0
    )
    base_level = base_mesh.max_level - minimum_level
    base_refinement = base_mesh.cell_levels_by_index(np.arange(base_mesh.nC))
    base_refinement[base_refinement > base_level] = base_level
    nested_mesh.insert_cells(
        base_mesh.gridCC,
        base_refinement,
        finalize=False,
    )

    tx_loops = []
    for source in survey.source_list:
        if isinstance(source, (TEMLineCurrent, FEMLineCurrent)):
            mesh_indices = get_intersecting_cells(source.location, base_mesh)
            tx_loops.append(base_mesh.cell_centers[mesh_indices, :])

    if tx_loops:
        locations = np.vstack([locations] + tx_loops)

    nested_mesh = insert_cells_by_locations(
        nested_mesh,
        base_mesh,
        locations,
        padding_cells=padding_cells,
        minimum_level=minimum_level,
        finalize=finalize,
    )

    return nested_mesh


def drape_to_octree(
    octree: Octree,
    drape_model: DrapeModel | list[DrapeModel],
    children: dict[str, list[str]],
    active: np.ndarray,
) -> Octree:
    """
    Interpolate drape model(s) into octree mesh.

    :param octree: Octree mesh to transfer values into
    :param drape_model: Drape model(s) whose values will be transferred
        into 'octree'.
    :param children: Dictionary containing a label and the associated
        names of the children in 'drape_model' to transfer into 'octree'.
    :param active: Active cell array for 'octree' model.

    :returns octree: Input octree mesh augmented with 'children' data from
        'drape_model' transferred onto cells using the prescribed 'method'.

    """
    if isinstance(drape_model, DrapeModel):
        drape_model = [drape_model]

    if any(len(v) != len(drape_model) for v in children.values()):
        raise ValueError(
            f"Number of names and drape models must match.  "
            f"Provided {len(children)} names and {len(drape_model)} models."
        )

    if octree.n_cells is None:
        raise ValueError("Octree mesh malformed. Finalize the mesh before use.")

    # create tree to search nearest neighbors in stacked drape model
    tree = cKDTree(np.vstack([d.centroids for d in drape_model]))
    _, lookup_inds = tree.query(octree.centroids)

    # perform interpolation using nearest neighbor or lookup method
    for label, names in children.items():
        drape_models = []

        for ind, model in enumerate(drape_model):
            datum = [k for k in model.children if k.name == names[ind]]
            if len(datum) > 1:
                raise ValueError(
                    f"Found more than one data set with name {names[ind]} in"
                    f"model {model.name}."
                )

            drape_models.append(datum[0].values)

        model_vector: np.ndarray = np.hstack(drape_models)[lookup_inds]

        if np.issubdtype(model_vector.dtype, np.integer):
            model_vector[~active] = INTEGER_NDV
        else:
            model_vector[~active] = np.nan  # apply active cells

        octree.add_data({label: {"values": model_vector}})

    return octree


def drape_2_tensor(drape_model: DrapeModel, return_sorting: bool = False) -> tuple:
    """
    Convert a geoh5 drape model to discretize.TensorMesh.

    :param: drape_model: geoh5py.DrapeModel object.
    :param: return_sorting: If True then return an index array that would
        re-sort a model in TensorMesh order to DrapeModel order.
    """
    if drape_model.prisms is None or drape_model.layers is None:
        raise ValueError("DrapeModel must contain prisms and layers.")

    prisms = drape_model.prisms
    layers = drape_model.layers
    z = np.append(np.unique(layers[:, 2]), prisms[:, 2].max())
    x = compute_alongline_distance(prisms[:, :2])
    dx = np.diff(x)
    end_core = [np.argmin(dx.round(1)), len(dx) - np.argmin(dx[::-1].round(1))]
    core = dx[end_core[0]]
    exp_fact = dx[0] / dx[1]
    cell_width = np.r_[
        core * exp_fact ** np.arange(end_core[0], 0, -1),
        core * np.ones(end_core[1] - end_core[0] + 1),
        core * exp_fact ** np.arange(1, len(dx) - end_core[1] + 1),
    ]
    h = [cell_width, np.diff(z)]
    origin = [-cell_width[: end_core[0]].sum(), layers[:, 2].min()]
    mesh = TensorMesh(h, origin)

    if return_sorting:
        sorting = np.arange(mesh.n_cells)
        sorting = sorting.reshape(mesh.shape_cells[1], mesh.shape_cells[0], order="C")
        sorting = sorting[::-1].T.flatten()
        return (mesh, sorting)

    return mesh


def floating_active(mesh: TensorMesh | TreeMesh, active: np.ndarray):
    """
    True if there are any active cells in the air

    :param mesh: Tree mesh object
    :param active: active cells array
    """
    if not isinstance(mesh, (TreeMesh, TensorMesh)):
        raise TypeError("Input mesh must be of type TreeMesh or TensorMesh.")

    if mesh.dim == 2:
        gradient = mesh.stencil_cell_gradient_y
    else:
        gradient = mesh.stencil_cell_gradient_z

    return any(gradient * active > 0)


class DrapeModelParameters(BaseModel):
    """
    Parameters for creating a drape model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    u_cell_size: float
    v_cell_size: float
    depth_core: float
    horizontal_padding: float
    vertical_padding: float
    expansion_factor: float
    name: str = "Models"
    parent: Group | None = None


def get_drape_model(
    workspace: Workspace,
    locations: np.ndarray,
    parameters: DrapeModelParameters,
) -> tuple[DrapeModel, TensorMesh]:
    """
    Create a BlockModel object from parameters.

    :param workspace: Workspace.
    :param locations: Location points.
    :param parameters: Parameters defining the DrapeModel mesh.

    :return object_out: Output block model.
    """

    locations = truncate_locs_depths(locations, parameters.depth_core)
    depth_core = minimum_depth_core(
        locations, parameters.depth_core, parameters.v_cell_size
    )

    mapper = DistanceMapper(locations, smoothing=2)
    profile = mapper.profile
    profile[:, -1] += (
        locations[:, 2].max() - profile[:, -1].max() + parameters.v_cell_size
    )
    mesh = mesh_utils.mesh_builder_xyz(
        profile,
        [parameters.u_cell_size, parameters.v_cell_size],
        padding_distance=[
            [parameters.horizontal_padding] * 2,
            [parameters.vertical_padding] * 2,
        ],
        depth_core=depth_core,
        expansion_factor=parameters.expansion_factor,
        mesh_type="tensor",
    )

    top = np.max(
        mesh.cell_centers[:, 1].reshape(len(mesh.h[1]), -1)[:, 0] + (mesh.h[1] / 2)
    )
    bottoms = mesh.cell_centers[:, 1].reshape(len(mesh.h[1]), -1)[:, 0] - (
        mesh.h[1] / 2
    )

    center_xy = mapper.map_locations(mesh.cell_centers_x)
    n_columns = center_xy.shape[0]
    n_layers = len(bottoms)

    prisms = np.c_[
        center_xy[:, :2],
        top * np.ones(n_columns),
        np.arange(0, n_layers * n_columns, n_layers),
        n_layers * np.ones(n_columns),
    ]
    layers = np.c_[
        np.kron(np.arange(n_columns), np.ones(n_layers)),
        np.tile(np.c_[np.arange(n_layers), bottoms[::-1]], (n_columns, 1)),
    ]

    drape_model = DrapeModel.create(
        workspace,
        layers=layers,
        name=parameters.name,
        parent=parameters.parent,
        prisms=prisms,
    )

    return drape_model, mesh


def get_containing_cells(
    mesh: TreeMesh | TensorMesh, data: InversionData
) -> np.ndarray:
    """
    Find indices of cells that contain data locations

    :param mesh: Computational mesh object
    :param data: Inversion data object
    """
    if isinstance(mesh, TreeMesh):
        inds = mesh._get_containing_cell_indexes(  # pylint: disable=protected-access
            data.locations
        )

        if isinstance(data.entity, LargeLoopGroundEMSurvey):
            line_ind = []
            transmitters = data.entity.transmitters
            for cell in transmitters.cells:
                line_ind.append(
                    mesh.get_cells_along_line(
                        transmitters.vertices[cell[0], :],
                        transmitters.vertices[cell[1], :],
                    )
                )
            inds = np.unique(np.r_[inds, np.hstack(line_ind)])

    elif isinstance(mesh, TensorMesh):
        locations = data.drape_locations(np.unique(data.locations, axis=0))
        xi = np.searchsorted(mesh.nodes_x, locations[:, 0]) - 1
        yi = np.searchsorted(mesh.nodes_y, locations[:, -1]) - 1
        inds = xi * mesh.shape_cells[1] + yi

    else:
        raise TypeError("Mesh must be 'TreeMesh' or 'TensorMesh'")

    return inds


def cell_size_z(drape_model: DrapeModel) -> np.ndarray:
    """Compute z cell sizes of drape model."""

    if drape_model.prisms is None or drape_model.layers is None:
        raise ValueError("DrapeModel must contain prisms and layers.")

    hz = []
    for prism in drape_model.prisms:
        top_z, top_layer, n_layers = prism[2:]
        bottoms = drape_model.layers[
            range(int(top_layer), int(top_layer + n_layers)), 2
        ]
        z = np.hstack([top_z, bottoms])
        hz.append(z[:-1] - z[1:])
    return np.hstack(hz)


def truncate_locs_depths(locs: np.ndarray, depth_core: float) -> np.ndarray:
    """
    Sets locations below core to core bottom.

    :param locs: Location points.
    :param depth_core: Depth of core mesh below locs.

    :return locs: locs with depths truncated.
    """
    zmax = locs[:, -1].max()  # top of locs
    below_core_ind = (zmax - locs[:, -1]) > depth_core
    core_bottom_elev = zmax - depth_core
    locs[
        below_core_ind, -1
    ] = core_bottom_elev  # sets locations below core to core bottom
    return locs


def minimum_depth_core(
    locs: np.ndarray, depth_core: float, core_z_cell_size: float
) -> float:
    """
    Get minimum depth core.

    :param locs: Location points.
    :param depth_core: Depth of core mesh below locs.
    :param core_z_cell_size: Cell size in z direction.

    :return depth_core: Minimum depth core.
    """
    zrange = locs[:, -1].max() - locs[:, -1].min()  # locs z range
    if depth_core >= zrange:
        return depth_core - zrange + core_z_cell_size

    return depth_core


def get_neighbouring_cells(mesh: TreeMesh, indices: list | np.ndarray) -> tuple:
    """
    Get the indices of neighbouring cells along a given axis for a given list of
    cell indices.

    :param mesh: discretize.TreeMesh object.
    :param indices: List of cell indices.

    :return: Two lists of neighbouring cell indices for every axis.
        axis[0] = (west, east)
        axis[1] = (south, north)
        axis[2] = (down, up)
    """
    if not isinstance(indices, (list, np.ndarray)):
        raise TypeError("Input 'indices' must be a list or numpy.ndarray of indices.")

    if not isinstance(mesh, TreeMesh):
        raise TypeError("Input 'mesh' must be a discretize.TreeMesh object.")

    neighbors: dict[int, list] = {ax: [[], []] for ax in range(mesh.dim)}

    for ind in indices:
        for ax in range(mesh.dim):
            neighbors[ax][0].append(np.r_[mesh[ind].neighbors[ax * 2]])
            neighbors[ax][1].append(np.r_[mesh[ind].neighbors[ax * 2 + 1]])

    return tuple(
        (np.r_[tuple(neighbors[ax][0])], np.r_[tuple(neighbors[ax][1])])
        for ax in range(mesh.dim)
    )
