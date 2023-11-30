#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
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

import warnings
from uuid import UUID

import numpy as np
from discretize import TreeMesh, TensorMesh
from geoapps_utils.numerical import traveling_salesman, running_mean, truncate_locs_depths, minimum_depth_core
from geoh5py import Workspace
from geoh5py.objects import DrapeModel, Octree
from geoh5py.shared import INTEGER_NDV
from octree_creation_app.utils import octree_2_treemesh
from scipy.interpolate import interp1d
from scipy.spatial import ConvexHull, cKDTree
from SimPEG.electromagnetics.frequency_domain.sources import (
    LineCurrent as FEMLineCurrent,
)
from SimPEG.electromagnetics.time_domain.sources import LineCurrent as TEMLineCurrent
from SimPEG.survey import BaseSurvey
from SimPEG.utils import mkvc

from simpeg_drivers.utils.surveys import get_intersecting_cells, get_unique_locations
from geoapps_utils.conversions import string_to_numeric
from simpeg_drivers.utils.surveys import compute_alongline_distance
from geoh5py.groups import Group
from discretize.utils import mesh_utils


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
            "Polynomial 'order' should be an integer > 0. "
            f"Value of {order} provided."
        )

    ind_nan = ~np.isnan(values)
    loc_xy = points[ind_nan, :]
    values = values[ind_nan]

    if method == "perimeter":
        hull = ConvexHull(loc_xy[:, :2])
        # Extract only those points that make the ConvexHull
        loc_xy = loc_xy[hull.vertices, :2]
        values = values[hull.vertices]
    elif not method == "all":
        raise ValueError(
            "'method' must be either 'all', or 'perimeter'. " f"Value {method} provided"
        )

    # Compute center of mass
    center_x = np.sum(loc_xy[:, 0] * np.abs(values)) / np.sum(np.abs(values))
    center_y = np.sum(loc_xy[:, 1] * np.abs(values)) / np.sum(np.abs(values))

    polynomial = []
    xx, yy = np.triu_indices(order + 1)
    for x, y in zip(xx, yy):
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
    for count, (x, y) in enumerate(zip(xx, yy)):
        data_trend += (
            params[count]
            * (points[:, 0] - center_x) ** float(x)
            * (points[:, 1] - center_y) ** float(y - x)
        )
    print(
        f"Removed {order}th order polynomial trend with mean: {np.mean(data_trend):.6g}"
    )
    return data_trend, params


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

    Parameters
    ----------

    locations: Array of coordinates for the local survey shape(*, 3).
    base_mesh: Input global TreeMesh object.
    padding_cells: Used for 'method'= 'padding_cells'. Number of cells in each concentric shell.
    minimum_level: Minimum octree level to preserve everywhere outside the local survey area.
    finalize: Return a finalized local treemesh.
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
    base_cell = np.min([base_mesh.h[0][0], base_mesh.h[1][0]])
    tx_loops = []
    for source in survey.source_list:
        if isinstance(source, (TEMLineCurrent, FEMLineCurrent)):
            mesh_indices = get_intersecting_cells(source.location, base_mesh)
            tx_loops.append(base_mesh.cell_centers[mesh_indices, :])

    if tx_loops:
        locations = np.vstack([locations] + tx_loops)

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
            if method == "nearest":
                octree_model.append(datum[0].values)
            else:
                lookup_inds = (
                    mesh._get_containing_cell_indexes(  # pylint: disable=W0212
                        model.centroids
                    )
                )
                octree_model[lookup_inds] = datum[0].values

        if method == "nearest":
            octree_model = np.hstack(octree_model)[lookup_inds]
        else:
            octree_model = octree_model[mesh._ubc_order]  # pylint: disable=W0212

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
    else:
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
    :param pads: len(6) Padding distances [W, E, N, S, Down, Up]
    :param expansion_factor: Expansion factor for padding cells.
    :param return_colocated_mesh: If true return TensorMesh.
    :param return_sorting: If true, return the indices required to map
        values stored in the TensorMesh to the drape model.

    :return object_out: Output block model.
    """

    locations = truncate_locs_depths(locations, depth_core)
    depth_core = minimum_depth_core(locations, depth_core, h[1])
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

    cc = mesh.cell_centers
    hz = mesh.h[1]
    top = np.max(cc[:, 1].reshape(len(hz), -1)[:, 0] + (hz / 2))
    bottoms = cc[:, 1].reshape(len(hz), -1)[:, 0] - (hz / 2)
    n_layers = len(bottoms)

    prisms = []
    layers = []
    indices = []
    index = 0
    center_xy = np.c_[x_interp(mesh.cell_centers_x), y_interp(mesh.cell_centers_x)]
    for i, (x_center, y_center) in enumerate(center_xy):
        prisms.append([float(x_center), float(y_center), top, i * n_layers, n_layers])
        for k, b in enumerate(bottoms):
            layers.append([i, k, b])
            indices.append(index)
            index += 1

    prisms = np.vstack(prisms)
    layers = np.vstack(layers)
    layers[:, 2] = layers[:, 2][::-1]

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
    val = [model]
    if return_colocated_mesh:
        val.append(mesh)
    if return_sorting:
        sorting = np.arange(mesh.n_cells)
        sorting = sorting.reshape(mesh.shape_cells[1], mesh.shape_cells[0], order="C")
        sorting = sorting[::-1].T.flatten()
        val.append(sorting)
    return val


def get_inversion_output(h5file: str | Workspace, inversion_group: str | UUID):
    """
    Recover inversion iterations from a ContainerGroup comments.
    """
    if isinstance(h5file, Workspace):
        workspace = h5file
    else:
        workspace = Workspace(h5file)

    try:
        group = workspace.get_entity(inversion_group)[0]
    except IndexError as exc:
        raise IndexError(
            f"BaseInversion group {inversion_group} could not be found in the target geoh5 {h5file}"
        ) from exc

    outfile = group.get_entity("SimPEG.out")[0]
    out = [l for l in outfile.values.decode("utf-8").replace("\r", "").split("\n")][:-1]
    cols = out.pop(0).split(" ")
    out = [[string_to_numeric(k) for k in l.split(" ")] for l in out]
    out = dict(zip(cols, list(map(list, zip(*out)))))

    return out


def tile_locations(
    locations,
    n_tiles,
    minimize=True,
    method="kmeans",
    bounding_box=False,
    count=False,
    unique_id=False,
):
    """
    Function to tile a survey points into smaller square subsets of points

    :param numpy.ndarray locations: n x 2 array of locations [x,y]
    :param integer n_tiles: number of tiles (for 'cluster'), or number of
        refinement steps ('other')
    :param Bool minimize: shrink tile sizes to minimum
    :param string method: set to 'kmeans' to use better quality clustering, or anything
        else to use more memory efficient method for large problems
    :param bounding_box: bool [False]
        Return the SW and NE corners of each tile.
    :param count: bool [False]
        Return the number of locations in each tile.
    :param unique_id: bool [False]
        Return the unique identifiers of all tiles.

    RETURNS:
    :param list: Return a list of arrays with the for the SW and NE
                        limits of each tiles
    :param integer binCount: Number of points in each tile
    :param list labels: Cluster index of each point n=0:(nTargetTiles-1)
    :param numpy.array tile_numbers: Vector of tile numbers for each count in binCount

    NOTE: All X Y and xy products are legacy now values, and are only used
    for plotting functions. They are not used in any calculations and could
    be dropped from the return calls in future versions.


    """

    if method == "kmeans":
        # Best for smaller problems

        np.random.seed(0)
        # Cluster
        # TODO turn off filter once sklearn has dealt with the issue causeing the warning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            from sklearn.cluster import KMeans

            cluster = KMeans(n_clusters=n_tiles, n_init="auto")
            cluster.fit_predict(locations[:, :2])

        labels = cluster.labels_

        # nData in each tile
        binCount = np.zeros(int(n_tiles))

        # x and y limits on each tile
        X1 = np.zeros_like(binCount)
        X2 = np.zeros_like(binCount)
        Y1 = np.zeros_like(binCount)
        Y2 = np.zeros_like(binCount)

        for ii in range(int(n_tiles)):
            mask = cluster.labels_ == ii
            X1[ii] = locations[mask, 0].min()
            X2[ii] = locations[mask, 0].max()
            Y1[ii] = locations[mask, 1].min()
            Y2[ii] = locations[mask, 1].max()
            binCount[ii] = mask.sum()

        xy1 = np.c_[X1[binCount > 0], Y1[binCount > 0]]
        xy2 = np.c_[X2[binCount > 0], Y2[binCount > 0]]

        # Get the tile numbers that exist, for compatibility with the next method
        tile_id = np.unique(cluster.labels_)

    else:
        # Works on larger problems
        # Initialize variables
        # Test each refinement level for maximum space coverage
        nTx = 1
        nTy = 1
        for ii in range(int(n_tiles + 1)):
            nTx += 1
            nTy += 1

            testx = np.percentile(locations[:, 0], np.arange(0, 100, 100 / nTx))
            testy = np.percentile(locations[:, 1], np.arange(0, 100, 100 / nTy))

            # if ii > 0:
            dx = testx[:-1] - testx[1:]
            dy = testy[:-1] - testy[1:]

            if np.mean(dx) > np.mean(dy):
                nTx -= 1
            else:
                nTy -= 1

            print(nTx, nTy)
        tilex = np.percentile(locations[:, 0], np.arange(0, 100, 100 / nTx))
        tiley = np.percentile(locations[:, 1], np.arange(0, 100, 100 / nTy))

        X1, Y1 = np.meshgrid(tilex, tiley)
        X2, Y2 = np.meshgrid(
            np.r_[tilex[1:], locations[:, 0].max()],
            np.r_[tiley[1:], locations[:, 1].max()],
        )

        # Plot data and tiles
        X1, Y1, X2, Y2 = mkvc(X1), mkvc(Y1), mkvc(X2), mkvc(Y2)
        binCount = np.zeros_like(X1)
        labels = np.zeros_like(locations[:, 0])
        for ii in range(X1.shape[0]):
            mask = (
                (locations[:, 0] >= X1[ii])
                * (locations[:, 0] <= X2[ii])
                * (locations[:, 1] >= Y1[ii])
                * (locations[:, 1] <= Y2[ii])
            ) == 1

            # Re-adjust the window size for tight fit
            if minimize:
                if mask.sum():
                    X1[ii], X2[ii] = (
                        locations[:, 0][mask].min(),
                        locations[:, 0][mask].max(),
                    )
                    Y1[ii], Y2[ii] = (
                        locations[:, 1][mask].min(),
                        locations[:, 1][mask].max(),
                    )

            labels[mask] = ii
            binCount[ii] = mask.sum()

        xy1 = np.c_[X1[binCount > 0], Y1[binCount > 0]]
        xy2 = np.c_[X2[binCount > 0], Y2[binCount > 0]]

        # Get the tile numbers that exist
        # Since some tiles may have 0 data locations, and are removed by
        # [binCount > 0], the tile numbers are no longer contiguous 0:nTiles
        tile_id = np.unique(labels)

    tiles = []
    for tid in tile_id.tolist():
        tiles += [np.where(labels == tid)[0]]

    out = [tiles]

    if bounding_box:
        out.append([xy1, xy2])

    if count:
        out.append(binCount[binCount > 0])

    if unique_id:
        out.append(tile_id)

    if len(out) == 1:
        return out[0]
    return tuple(out)
