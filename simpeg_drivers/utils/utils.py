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

from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
from discretize import TensorMesh, TreeMesh
from discretize.utils import mesh_utils
from geoapps_utils.utils.locations import mask_under_horizon
from geoapps_utils.utils.numerical import running_mean, traveling_salesman
from geoh5py import Workspace
from geoh5py.data import NumericData
from geoh5py.groups import Group, SimPEGGroup
from geoh5py.objects import DrapeModel, Octree
from geoh5py.objects.surveys.direct_current import PotentialElectrode
from geoh5py.objects.surveys.electromagnetics.base import LargeLoopGroundEMSurvey
from geoh5py.shared import INTEGER_NDV
from geoh5py.ui_json import InputFile
from grid_apps.utils import octree_2_treemesh
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator, interp1d
from scipy.spatial import ConvexHull, Delaunay, cKDTree

from simpeg_drivers import DRIVER_MAP
from simpeg_drivers.utils.surveys import (
    compute_alongline_distance,
)


if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData
    from simpeg_drivers.driver import InversionDriver


def calculate_2D_trend(
    points: np.ndarray, values: np.ndarray, order: int = 0, method: str = "all"
):
    """
    detrend2D(points, values, order=0, method='all')

    Function to remove a trend from 2D scatter points with values

    Parameters:
    ----------

    points: array or floats, shape(*, 2)
        Coordinates of input points

    values: array of floats, shape(*,)
        Values to be de-trended

    order: Order of the polynomial to be used

    method: str
        Method to be used for the detrending
            "all": USe all points
            "perimeter": Only use points on the convex hull


    Returns
    -------

    trend: array of floats, shape(*,)
        Calculated trend

    coefficients: array of floats, shape(order+1)
        Coefficients for the polynomial describing the trend

        trend = c[0] + points[:, 0] * c[1] +  points[:, 1] * c[2]
    """
    if not isinstance(order, int) or order < 0:
        raise ValueError(
            f"Polynomial 'order' should be an integer > 0. Value of {order} provided."
        )

    ind_nan = ~np.isnan(values)
    loc_xy = points[ind_nan, :]
    values = values[ind_nan]

    if method == "perimeter":
        hull = ConvexHull(loc_xy[:, :2])
        # Extract only those points that make the ConvexHull
        loc_xy = loc_xy[hull.vertices, :2]
        values = values[hull.vertices]
    elif method != "all":
        raise ValueError(
            f"'method' must be either 'all', or 'perimeter'. Value {method} provided"
        )

    # Compute center of mass
    center_x = np.sum(loc_xy[:, 0] * np.abs(values)) / np.sum(np.abs(values))
    center_y = np.sum(loc_xy[:, 1] * np.abs(values)) / np.sum(np.abs(values))

    polynomial = []
    xx, yy = np.triu_indices(order + 1)
    for x, y in zip(xx, yy, strict=True):
        polynomial.append(
            (loc_xy[:, 0] - center_x) ** float(x)
            * (loc_xy[:, 1] - center_y) ** float(y - x)
        )
    polynomial = np.vstack(polynomial).T

    if polynomial.shape[0] <= polynomial.shape[1]:
        raise ValueError(
            "The number of input values must be greater than the number of coefficients in the polynomial. "
            f"Provided {polynomial.shape[0]} values for a {order}th order polynomial with {polynomial.shape[1]} coefficients."
        )

    params, _, _, _ = np.linalg.lstsq(polynomial, values, rcond=None)
    data_trend = np.zeros(points.shape[0])
    for count, (x, y) in enumerate(zip(xx, yy, strict=True)):
        data_trend += (
            params[count]
            * (points[:, 0] - center_x) ** float(x)
            * (points[:, 1] - center_y) ** float(y - x)
        )
    print(
        f"Removed {order}th order polynomial trend with mean: {np.mean(data_trend):.6g}"
    )
    return data_trend, params


def drape_to_octree(
    octree: Octree,
    drape_model: DrapeModel | list[DrapeModel],
    children: dict[str, list[str]],
    active: np.ndarray,
    method: str = "lookup",
) -> Octree:
    """
    Interpolate drape model(s) into octree mesh.

    :param octree: Octree mesh to transfer values into
    :param drape_model: Drape model(s) whose values will be transferred
        into 'octree'.
    :param children: Dictionary containing a label and the associated
        names of the children in 'drape_model' to transfer into 'octree'.
    :param active: Active cell array for 'octree' model.
    :param method: Use 'lookup' to for a containing cell lookup method, or
        'nearest' for a nearest neighbor search method to transfer values

    :returns octree: Input octree mesh augmented with 'children' data from
        'drape_model' transferred onto cells using the prescribed 'method'.

    """
    if method not in ["nearest", "lookup"]:
        raise ValueError(f"Method must be 'nearest' or 'lookup'.  Provided {method}.")

    if isinstance(drape_model, DrapeModel):
        drape_model = [drape_model]

    if any(len(v) != len(drape_model) for v in children.values()):
        raise ValueError(
            f"Number of names and drape models must match.  "
            f"Provided {len(children)} names and {len(drape_model)} models."
        )

    if method == "nearest":
        # create tree to search nearest neighbors in stacked drape model
        tree = cKDTree(np.vstack([d.centroids for d in drape_model]))
        _, lookup_inds = tree.query(octree.centroids)
    else:
        mesh = octree_2_treemesh(octree)

    # perform interpolation using nearest neighbor or lookup method
    for label, names in children.items():
        octree_model = (
            [] if method == "nearest" else np.array([np.nan] * octree.n_cells)
        )
        for ind, model in enumerate(drape_model):
            datum = [k for k in model.children if k.name == names[ind]]
            if len(datum) > 1:
                raise ValueError(
                    f"Found more than one data set with name {names[ind]} in"
                    f"model {model.name}."
                )

            if not isinstance(datum[0], NumericData):
                continue

            if method == "nearest":
                octree_model.append(datum[0].values)
            else:
                lookup_inds = mesh.get_containing_cells(model.centroids)
                octree_model[lookup_inds] = datum[0].values

        if len(octree_model) == 0:
            continue

        if method == "nearest":
            octree_model = np.hstack(octree_model)[lookup_inds]

        if np.issubdtype(octree_model.dtype, np.integer):
            octree_model[~active] = INTEGER_NDV
        else:
            octree_model[~active] = np.nan  # apply active cells

        octree.add_data({label: {"values": octree_model}})

    return octree


def drape_2_tensor(drape_model: DrapeModel, return_sorting: bool = False) -> tuple:
    """
    Convert a geoh5 drape model to discretize.TensorMesh.

    :param: drape_model: geoh5py.DrapeModel object.
    :param: return_sorting: If True then return an index array that would
        re-sort a model in TensorMesh order to DrapeModel order.
    """
    prisms = drape_model.prisms
    layers = drape_model.layers

    # Deal with ghost points
    ghosts = prisms[:, -1] == 1
    prisms = prisms[~ghosts, :]

    nu_layers = np.unique(prisms[:, -1])
    if len(nu_layers) > 1:
        raise ValueError(
            "Drape model conversion to TensorMesh must have uniform number of layers."
        )

    n_layers = nu_layers[0].astype(int)
    filt_layers = ghosts[layers[:, 0].astype(int)]
    layers = layers[~filt_layers, :]

    hz = np.r_[
        prisms[0, 2] - layers[0, 2],
        -np.diff(layers[:n_layers, 2]),
    ][::-1]

    x = compute_alongline_distance(prisms[:, :2], ordered=False)
    dx = np.diff(x)
    cell_width = np.r_[dx[0], (dx[:-1] + dx[1:]) / 2.0, dx[-1]]
    h = [cell_width, hz]
    origin = [0, layers[:, 2].min()]
    mesh = TensorMesh(h, origin=origin)

    if return_sorting:
        sorting = np.arange(mesh.n_cells)
        sorting = sorting.reshape(mesh.shape_cells[1], mesh.shape_cells[0], order="C")
        sorting = np.argsort(sorting[::-1].T.flatten())

        # Skip indices for ghost points
        count = -1
        for ghost in ghosts:
            if ghost:
                sorting[sorting > count] += 1
                count += 1
            else:
                count += n_layers

        return (mesh, sorting)
    else:
        return mesh


def floating_active(mesh: TensorMesh | TreeMesh, active: np.ndarray):
    """
    True if there are any active cells in the air

    :param mesh: Tree mesh object
    :param active: active cells array
    """
    if not isinstance(mesh, TreeMesh | TensorMesh):
        raise TypeError("Input mesh must be of type TreeMesh or TensorMesh.")

    if mesh.dim == 2:
        gradient = mesh.stencil_cell_gradient_y
    else:
        gradient = mesh.stencil_cell_gradient_z

    return any(gradient * active > 0)


def get_drape_model(
    workspace: Workspace,
    name: str,
    locations: np.ndarray,
    h: list,
    depth_core: float,
    pads: list,
    expansion_factor: float,
    parent: Group | None = None,
    return_colocated_mesh: bool = False,
    return_sorting: bool = False,
) -> tuple:
    """
    Create a BlockModel object from parameters.

    :param workspace: Workspace.
    :param parent: Group to contain the result.
    :param name: Block model name.
    :param locations: Location points.
    :param h: Cell size(s) for the core mesh.
    :param depth_core: Depth of core mesh below locs.
    :param pads: len(4) Padding distances [W, E, Down, Up]
    :param expansion_factor: Expansion factor for padding cells.
    :param return_colocated_mesh: If true return TensorMesh.
    :param return_sorting: If true, return the indices required to map
        values stored in the TensorMesh to the drape model.
    :return object_out: Output block model.
    """
    locations = truncate_locs_depths(locations, depth_core)
    order = traveling_salesman(locations)

    # Smooth the locations
    xy_smooth = np.vstack(
        [
            np.c_[locations[order[0], :]].T,
            np.c_[
                running_mean(locations[order, 0], 2),
                running_mean(locations[order, 1], 2),
                running_mean(locations[order, 2], 2),
            ],
            np.c_[locations[order[-1], :]].T,
        ]
    )
    distances = compute_alongline_distance(xy_smooth)
    distances[:, -1] += locations[:, 2].max() - distances[:, -1].max() + h[1]
    x_interp = interp1d(distances[:, 0], xy_smooth[:, 0], fill_value="extrapolate")
    y_interp = interp1d(distances[:, 0], xy_smooth[:, 1], fill_value="extrapolate")

    mesh = mesh_utils.mesh_builder_xyz(
        distances,
        h,
        padding_distance=[
            [pads[0], pads[1]],
            [pads[2], pads[3]],
        ],
        depth_core=depth_core,
        expansion_factor=expansion_factor,
        mesh_type="tensor",
    )
    hz = mesh.h[1][::-1]
    top = np.ones_like(mesh.cell_centers_x) * (mesh.origin[1] + np.sum(hz))
    locations_top = np.c_[
        x_interp(mesh.cell_centers_x), y_interp(mesh.cell_centers_x), top
    ]
    model = xyz_2_drape_model(workspace, locations_top, hz, name, parent)
    val = [model]
    if return_colocated_mesh:
        val.append(mesh)
    if return_sorting:
        sorting = np.arange(mesh.n_cells)
        sorting = sorting.reshape(mesh.shape_cells[1], mesh.shape_cells[0], order="C")
        sorting = sorting[::-1].T.flatten()
        val.append(sorting)
    return val


def xyz_2_drape_model(
    workspace, locations, depths, name=None, parent=None
) -> DrapeModel:
    """
    Convert a list of cell tops and layer depths to a DrapeModel object.

    :param workspace: Workspace object
    :param locations: n x 3 array of cell centers [x, y, z_top]
    :param depths: n x 1 array of layer depths
    :param name: Name of the new DrapeModel object
    :param parent: Parent group for the new DrapeModel object

    :returns: DrapeModel object
    """
    n_layers = len(depths)
    prisms = []
    layers = []
    indices = []
    index = 0

    for i, (x_center, y_center, z_top) in enumerate(locations):
        prisms.append([float(x_center), float(y_center), z_top, i * n_layers, n_layers])
        bottom = z_top
        for k, h in enumerate(depths):
            bottom -= h
            layers.append([i, k, bottom])
            indices.append(index)
            index += 1

    prisms = np.vstack(prisms)
    layers = np.vstack(layers)
    model = DrapeModel.create(
        workspace, layers=layers, name=name, prisms=prisms, parent=parent
    )
    model.add_data(
        {
            "indices": {
                "values": np.array(indices, dtype=np.int32),
                "association": "CELL",
            }
        }
    )
    return model


def get_containing_cells(
    mesh: TreeMesh | TensorMesh, data: InversionData
) -> np.ndarray:
    """
    Find indices of cells that contain data locations

    :param mesh: Computational mesh object
    :param data: Inversion data object
    """
    if isinstance(mesh, TreeMesh):
        if isinstance(data.entity, PotentialElectrode):
            potentials = data.entity.vertices
            currents = data.entity.current_electrodes.vertices
            locations = np.unique(np.r_[potentials, currents], axis=0)
        else:
            locations = data.locations

        inds = mesh.get_containing_cells(locations)

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
        inds = xi + yi * mesh.shape_cells[0]

    else:
        raise TypeError("Mesh must be 'TreeMesh' or 'TensorMesh'")

    return inds


def cell_size_z(drape_model: DrapeModel) -> np.ndarray:
    """Compute z cell sizes of drape model."""
    hz = []
    for prism in drape_model.prisms:
        top_z, top_layer, n_layers = prism[2:]
        bottoms = drape_model.layers[
            range(int(top_layer), int(top_layer + n_layers)), 2
        ]
        z = np.hstack([top_z, bottoms])
        hz.append(z[:-1] - z[1:])
    return np.hstack(hz)


def active_from_xyz(
    mesh: DrapeModel | Octree, topo: np.ndarray, grid_reference="center"
):
    """Returns an active cell index array below a surface

    :param mesh: Mesh object
    :param topo: Array of xyz locations
    :param grid_reference: Cell reference. Must be "center", "top", or "bottom"
    :param method: Interpolation method. Must be "linear", or "nearest"
    """

    mesh_dim = 2 if isinstance(mesh, DrapeModel) else 3
    locations = mesh.centroids.copy()

    if mesh_dim == 2:
        z_offset = cell_size_z(mesh) / 2.0
    else:
        z_offset = mesh.octree_cells["NCells"] * np.abs(mesh.w_cell_size) / 2

    # Shift cell center location to top or bottom of cell
    if grid_reference == "top":
        locations[:, -1] += z_offset
    elif grid_reference == "bottom":
        locations[:, -1] -= z_offset
    elif grid_reference == "center":
        pass
    else:
        raise ValueError("'grid_reference' must be one of 'center', 'top', or 'bottom'")

    # Return the active cell array
    return mask_under_horizon(locations, topo)


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
    locs[below_core_ind, -1] = (
        core_bottom_elev  # sets locations below core to core bottom
    )
    return locs


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
    if not isinstance(indices, list | np.ndarray):
        raise TypeError("Input 'indices' must be a list or numpy.ndarray of indices.")

    if not isinstance(mesh, TreeMesh):
        raise TypeError("Input 'mesh' must be a discretize.TreeMesh object.")

    neighbors = {ax: [[], []] for ax in range(mesh.dim)}

    for ind in indices:
        for ax in range(mesh.dim):
            neighbors[ax][0].append(np.r_[mesh[ind].neighbors[ax * 2]])
            neighbors[ax][1].append(np.r_[mesh[ind].neighbors[ax * 2 + 1]])

    return tuple(
        (np.r_[tuple(neighbors[ax][0])], np.r_[tuple(neighbors[ax][1])])
        for ax in range(mesh.dim)
    )


def simpeg_group_to_driver(group: SimPEGGroup, workspace: Workspace) -> InversionDriver:
    """
    Utility to generate an inversion driver from a SimPEG group options.

    :param group: SimPEGGroup object.
    :param workspace: Workspace object.
    """

    ui_json = deepcopy(group.options)
    ui_json["geoh5"] = workspace

    ifile = InputFile(ui_json=ui_json)
    forward_only = ui_json.get("forward_only", False)
    mod_name, classes = DRIVER_MAP.get(ui_json["inversion_type"])
    if forward_only:
        class_name = classes.get("forward", classes["inversion"])
    else:
        class_name = classes.get("inversion")
    module = __import__(mod_name, fromlist=[class_name])
    inversion_driver = getattr(module, class_name)

    ifile.set_data_value("out_group", group)
    params = inversion_driver._params_class.build(ifile)  # pylint: disable=protected-access

    return inversion_driver(params)
