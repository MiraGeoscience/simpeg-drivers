# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import contextlib
import cProfile
import multiprocessing
import pstats
import sys
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from dask.distributed import Client, LocalCluster, performance_report
from discretize import TensorMesh, TreeMesh
from discretize.utils import mesh_utils
from geoapps_utils.base import Options
from geoapps_utils.run import load_ui_json_as_dict
from geoapps_utils.utils.locations import mask_under_horizon
from geoapps_utils.utils.numerical import running_mean, traveling_salesman
from geoh5py import Workspace
from geoh5py.data import NumericData
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import DrapeModel, Octree
from geoh5py.objects.surveys.direct_current import PotentialElectrode
from geoh5py.objects.surveys.electromagnetics.airborne_app_con import (
    AirborneAppConReceivers,
)
from geoh5py.objects.surveys.electromagnetics.base import LargeLoopGroundEMSurvey
from geoh5py.shared import INTEGER_NDV
from geoh5py.shared.utils import fetch_active_workspace, mask_by_extent, stringify
from geoh5py.ui_json import InputFile
from grid_apps.utils import octree_2_treemesh
from scipy.interpolate import interp1d
from scipy.spatial import ConvexHull, cKDTree

from simpeg_drivers import DRIVER_MAP


if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData
    from simpeg_drivers.driver import InversionDriver


def mask_vertices_and_cells(
    extent: np.ndarray, vertices: np.ndarray, cells: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray] | tuple[np.ndarray, None]:
    """
    Mask vertices and remove cells whose vertices are all outside the extent.

    :param extent: Array of shape (2, 3) containing the lower SW and upper NE coordinates.
    :param vertices: Array of shape (n_vertices, 3) containing the x, y, z coordinates.
    :param cells: Array of shape (n_cells, 3) containing the indices of the vertices
        that make up each cell.
    """

    vertex_mask = mask_by_extent(vertices, extent=extent)

    if cells is None:
        return vertices[vertex_mask], None

    cell_mask = np.any(vertex_mask[cells], axis=1)
    vertex_mask = np.zeros_like(vertex_mask, dtype=bool)
    vertex_mask[cells[cell_mask].flatten()] = True

    new_cells = cells.copy()[cell_mask]
    cell_map = np.arange(len(vertices))[vertex_mask]
    new_cells = np.searchsorted(cell_map, new_cells)

    return vertices[vertex_mask], new_cells


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

    If ghost prisms are present in the drape model, they will be skipped and the resulting
    TensorMesh will have fewer cells than the DrapeModel, assuming a continuous
    TensorMesh with no ghost cells.

    :param: drape_model: geoh5py.DrapeModel object.
    :param: return_sorting: If True then return an index array that would
        re-sort a model in TensorMesh order to DrapeModel order.
    """
    prisms = drape_model.prisms
    layers = drape_model.layers

    # Deal with ghost points
    actives = prisms[:, -1] != 1

    nu_layers = np.unique(prisms[actives, -1])
    if len(nu_layers) > 1:
        raise ValueError(
            "Drape model conversion to TensorMesh must have uniform number of layers."
        )

    n_layers = nu_layers[0].astype(int)
    n_columns = actives.sum()

    # Sorting array from DrapeModel to TensorMesh order row-wise, skipping ghost points
    sorting = np.arange(n_columns * n_layers)
    sorting = sorting.reshape(n_layers, n_columns, order="C")
    sorting = np.argsort(sorting[::-1].T.flatten())

    filt_layers = actives[layers[:, 0].astype(int)]
    layers = layers[filt_layers, :]
    hz = np.r_[
        prisms[0, 2] - layers[0, 2],
        -np.diff(layers[:n_layers, 2]),
    ][::-1]

    # Skip indices for ghost points
    count = -1
    part = 0
    parts = []
    cell_widths = []
    section = []
    for ii, active in enumerate(actives):
        if not active:
            sorting[sorting > count] += 1
            count += 1

            if section:
                cell_widths.append(cell_width_from_centers(np.vstack(section)))
                parts.append(np.full(len(section), part))
                section = []
                part += 1
        else:
            section.append(np.c_[prisms[ii, 0], 0])
            count += n_layers

    cell_widths.append(cell_width_from_centers(np.vstack(section)))
    parts.append(np.full(len(section), part))

    h = [np.hstack(cell_widths), hz]
    origin = [0, prisms[0, 2] - hz.sum()]
    mesh = TensorMesh(h, origin=origin)
    mesh.parts = np.hstack(parts)  # Assign part numbers to cells

    if return_sorting:
        return (mesh, sorting)

    return mesh


def cell_width_from_centers(centers: np.ndarray) -> np.ndarray:
    """
    Compute cell widths from cell center locations.

    :param centers: n x 3 array of cell center locations

    :returns: Array of cell widths
    """
    x = compute_alongline_distance(centers[:, :2])
    half_dx = np.diff(x) / 2.0
    return np.r_[half_dx[0] * 2, (half_dx[:-1] + half_dx[1:]), half_dx[-1] * 2]


def floating_active(mesh: TensorMesh | TreeMesh, active: np.ndarray) -> bool:
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
    locations: np.ndarray,
    h: list,
    depth_core: float,
    pads: list,
    expansion_factor: float,
    return_colocated_mesh: bool = False,
    **object_kwargs,
) -> DrapeModel | tuple[DrapeModel, TensorMesh]:
    """
    Create a BlockModel object from parameters.

    :param workspace: Workspace.
    :param locations: Location points.
    :param h: Cell size(s) for the core mesh.
    :param depth_core: Depth of core mesh below locs.
    :param pads: len(4) Padding distances [W, E, Down, Up]
    :param expansion_factor: Expansion factor for padding cells.
    :param return_colocated_mesh: If true return TensorMesh.
    :param object_kwargs: Extra arguments to pass to the DrapeModel.create() method.

    :return object_out: Output block model.
    """
    order = traveling_salesman(locations)

    # Smooth the locations
    xyz_smooth = np.c_[
        running_mean(locations[order, 0], 2),
        running_mean(locations[order, 1], 2),
        running_mean(locations[order, 2], 2),
    ]

    # Rescale extent
    min_locs = locations.min(axis=0)
    max_locs = locations.max(axis=0)
    xyz_smooth -= xyz_smooth.min(axis=0)[None, :]
    xyz_smooth *= ((max_locs - min_locs) / np.maximum(xyz_smooth.max(axis=0), 1e-3))[
        None, :
    ]
    xyz_smooth += min_locs[None, :]

    distances = compute_alongline_distance(xyz_smooth)
    x_interp = interp1d(distances[:, 0], xyz_smooth[:, 0], fill_value="extrapolate")
    y_interp = interp1d(distances[:, 0], xyz_smooth[:, 1], fill_value="extrapolate")

    # Round the values for mesh creation to avoid issue with floor (int) rounding
    limits = np.vstack(
        [
            np.floor(distances.min(axis=0)),
            np.ceil(distances.max(axis=0)),
        ]
    )

    mesh = mesh_utils.mesh_builder_xyz(
        limits,
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
    drape_model = xyz_2_drape_model(workspace, locations_top, hz, **object_kwargs)

    if return_colocated_mesh:
        return drape_model, mesh
    return drape_model


def xyz_2_drape_model(workspace, locations, depths, **object_kwargs) -> DrapeModel:
    """
    Convert a list of cell tops and layer depths to a DrapeModel object.

    :param workspace: Workspace object
    :param locations: n x 3 array of cell centers [x, y, z_top]
    :param depths: n x 1 array of layer depths
    :param object_kwargs: Additional keyword arguments to pass to DrapeModel.create()

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
    model = DrapeModel.create(workspace, layers=layers, prisms=prisms, **object_kwargs)
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

    :returns: Array of unique cell indices that contain data locations
    """
    if isinstance(mesh, TreeMesh):
        if isinstance(data.entity, PotentialElectrode):
            potentials = data.entity.vertices
            currents = data.entity.current_electrodes.vertices
            locations = np.unique(np.r_[potentials, currents], axis=0)
        elif isinstance(data.entity, AirborneAppConReceivers):
            locations = data.entity.base_stations.vertices
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
            inds = np.r_[inds, np.hstack(line_ind)]

    elif isinstance(mesh, TensorMesh):
        locations = data.drape_locations(np.unique(data.locations, axis=0))
        xi = np.searchsorted(mesh.nodes_x, locations[:, 0]) - 1
        yi = np.searchsorted(mesh.nodes_y, locations[:, -1]) - 1
        inds = xi + yi * mesh.shape_cells[0]

    else:
        raise TypeError("Mesh must be 'TreeMesh' or 'TensorMesh'")

    return np.unique(inds)


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
    mesh: DrapeModel | Octree,
    topo: np.ndarray,
    grid_reference="center",
    triangulation: np.ndarray | None = None,
) -> np.ndarray:
    """Returns an active cell index array below a surface

    :param mesh: Mesh object
    :param topo: Array of xyz locations
    :param grid_reference: Cell reference. Must be "center", "top", or "bottom"
    :param method: Interpolation method. Must be "linear", or "nearest"

    :return: Array of active cell indices below the surface defined by 'topo'.
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
    return mask_under_horizon(locations, horizon=topo, triangulation=triangulation)


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

    :returns: InversionDriver object.
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


def compute_alongline_distance(points: np.ndarray, ordered: bool = True) -> np.ndarray:
    """
    Convert from cartesian (x, y, values) points to (distance, values) locations.

    :param points: Cartesian coordinates of points lying either roughly within a
        plane or a line.
    :param ordered: Flag to indicate whether points are already ordered along a line.
        If False, then the points will be ordered using a traveling salesman algorithm
        before computing distances.

    :returns: Array of shape (n_points, n_features) where the first column contains
        distances along the line and the remaining columns contain the corresponding
        values from the input 'points' array.
    """
    if not ordered:
        order = traveling_salesman(points)
        points = points[order, :]

    distances = np.cumsum(
        np.r_[0, np.linalg.norm(np.diff(points[:, :2], axis=0), axis=1)]
    )
    if points.shape[1] > 2:
        distances = np.c_[distances, points[:, 2:]]

    return distances


def get_default_parallelization_params(json_path: Path) -> tuple[int, int]:
    """
    Get parallelization parameters from a ui_json file.

    If the number of workers is unset, it is estimated from the number of CPU cores.

    :param json_path: Path to ui_json file.
    :returns: Tuple of parallelization parameters.
    """
    ui_json = load_ui_json_as_dict(json_path)

    n_workers = ui_json.get("n_workers", None)
    n_threads = ui_json.get("n_threads", None)

    if n_workers is None:
        cpu_count = multiprocessing.cpu_count()

        if cpu_count < 16:
            n_threads = n_threads or 2
        else:
            n_threads = n_threads or 4

        n_workers = cpu_count // n_threads

    return n_workers, n_threads


def validate_out_group(options: Options) -> SimPEGGroup:
    """
    Validate or create a SimPEGGroup to store results.

    :param out_group: Output group from selection.
    """
    if isinstance(options.out_group, SimPEGGroup):
        return options.out_group

    with fetch_active_workspace(options.geoh5, mode="r+"):
        out_group = SimPEGGroup.create(
            options.geoh5,
            name=options.title,
        )
        out_group.entity_type.name = options.title
        options = options.model_copy(update={"out_group": out_group})
        out_group.options = stringify(options.input_file.ui_json)
        out_group.metadata = None

    return out_group


def start_dask_run(
    class_type,
    json_path: Path,
    n_workers: int | None = None,
    n_threads: int | None = None,
):
    """
    Sets Dask config settings.

    :param json_path: Path to input file (.ui.json) for the application.
    :param n_workers: Number of workers to use.
    :param n_threads: Number of threads to use.
    """
    ui_json = load_ui_json_as_dict(json_path)

    n_workers = ui_json.get("n_workers", n_workers)
    n_threads = ui_json.get("n_threads", n_threads)
    save_report = ui_json.get("performance_report", False)

    if (n_workers is not None and n_workers > 1) or n_threads is not None:
        cluster = LocalCluster(
            processes=True,
            n_workers=n_workers,
            threads_per_worker=n_threads,
        )
    else:
        cluster = None

    profiler = cProfile.Profile()
    profiler.enable()

    with (
        cluster.get_client()
        if cluster is not None
        else contextlib.nullcontext() as context_client
    ):
        # Full run
        with (
            performance_report(filename=json_path.parent / "dask_profile.html")
            if (save_report and isinstance(context_client, Client))
            else contextlib.nullcontext()
        ):
            class_type.start(json_path)
            sys.stdout.close()

    profiler.disable()

    if save_report:
        with open(
            json_path.parent / "runtime_profile.txt", encoding="utf-8", mode="w"
        ) as s:
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats("cumulative")
            ps.print_stats()
