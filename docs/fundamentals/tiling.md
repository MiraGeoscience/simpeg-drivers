# Tiling and Nested Meshes

This section describes how `simpeg-drivers` decomposes a large geophysical
problem into smaller sub-problems ("tiles"), and how a dedicated local
("nested") mesh is built for each tile from the single global inversion
mesh. Tiling is the mechanism that makes large inversions tractable and
parallelizable (see also [Parallelization](parallelization.md)).

The logic is split across three layers:

- **Driver layer** (`simpeg_drivers/driver.py`,
  `electricals/base_2d.py`, `electromagnetics/base_1d_driver.py`) —
  decides *which* data points go into *which* tile.
- **Factory layer** (`components/factories/misfit_factory.py`) —
  turns tiles into a global, optionally distributed, data-misfit
  function.
- **Nested-mesh utilities** (`simpeg_drivers/utils/nested.py`) — builds
  the local survey, local mesh, model mapping and local simulation for a
  single tile.

A companion tool, the **tile estimator**
(`simpeg_drivers/utils/tile_estimate.py`), helps choose a good number of
tiles up front.

## Overview

The inversion works with a single *global* mesh and a single global model
defined on its active cells. Evaluating the full sensitivity/forward
problem on that global mesh for every receiver at once is memory- and
compute-intensive. Instead, the problem is tiled:

1. The receiver locations are partitioned into `tile_spatial` groups.
2. Each group gets a **nested mesh**: a copy of the global mesh that keeps
   the fine octree refinement only around that tile's receivers (and
   source wire paths), and is coarsened everywhere else.
3. A local simulation is built on the nested mesh, with a `TileMap` that
   projects the *global active model* onto the *local active cells*.
4. All local data misfits are summed into a single
   `ComboObjectiveFunction` (or a `DistributedComboMisfits` when running
   with Dask workers).

Because each tile shares the global mesh extent and alignment, the
`TileMap` can cheaply move between the global model and each local mesh,
so a single model is still being inverted even though the forward
problems run on many small meshes.

## Step 1 — Tiling the locations

### Clustering (`tile_locations`)

`simpeg_drivers.utils.nested.tile_locations` partitions survey points into
`n_tiles` spatially compact subsets. It returns a list of index arrays,
one per tile.

- **Curve-based splitting.** If `labels` (e.g. survey line/part ids) are
  provided and the number of unique labels is `>= n_tiles`, the labels
  themselves are split evenly (`np.array_split`) into `n_tiles` groups.
  This keeps whole lines/parts together — important for 2D/line data.
- **Point-based splitting.** Otherwise it falls back to a `KMeans`
  clustering on the X/Y coordinates. Coordinates are normalized to
  `[0, 1]`, and any labels are appended as extra clustering features so
  that points from the same label tend to cluster together. A fixed
  `random_state=0` makes the tiling reproducible.

### Driver-level tiling (`get_tiles`)

The base driver (`InversionDriver.get_tiles`) calls `tile_locations` with:

- `self.inversion_data.locations` — the receiver locations,
- `self.params.compute.tile_spatial` — the requested tile count,
- `labels=self.inversion_data.parts` — survey parts,
- `sorting=self.simulation.survey.sorting`.

The resulting tiles are then:

- Passed through `split_list`, which further sub-splits tiles so the total
  number of misfit chunks divides evenly across Dask `workers` (preserving
  the mesh — see below). Without workers, each tile becomes a single
  `[tile]`.
- Duplicated per **channel** for frequency-domain methods (`apparent
  conductivity`, `magnetotellurics`, `tipper`, `fdem`), where
  `channels = survey.frequencies`; otherwise a single `None` channel is
  used.

The return value is a dictionary `{channel: [[sub_indices, ...], ...]}`.

### Method-specific tiling

- **2D electricals** (`electricals/base_2d.py::get_tiles`): one tile per
  selected survey *part* (line), i.e. `np.where(line_parts == part)`.
  Line data is never clustered across lines.
- **1D EM** (`electromagnetics/base_1d_driver.py::get_tiles`): tiles are
  simple `np.array_split` chunks of the sounding indices, sized by
  `max_chunk_size` and the number of workers (a heuristic to avoid too
  many small chunks).

## Step 2 — Building the global misfit (`MisfitFactory`)

`MisfitFactory.assemble_arguments` walks the `{channel: [tiles]}`
dictionary and, for every `sub_indices` chunk, calls
`create_misfit` (locally, or submitted to a Dask worker round-robin).
Key details:

- The global `simulation` is **pickled to a temporary file** so it can be
  shipped to workers; each misfit task reloads it.
- Each chunk is passed `np.hstack(tile)` as `shared_indices` — all
  sub-chunks of the same original tile build their **shared nested mesh**
  from the same set of indices (so sub-splitting for load balancing does
  not change the mesh).
- Local survey orderings are collected back and reassembled into
  `simulation.survey.ordering` so predicted data can be mapped back to the
  global data vector.
- With a client, the result is a
  `DistributedComboMisfits`; otherwise a plain
  `ComboObjectiveFunction` of `L2DataMisfit` terms.

## Step 3 — Creating the nested mesh

All nested-mesh construction goes through
`create_nested_mesh(survey, base_mesh, **kwargs)`, which dispatches by
mesh type:

- `TreeMesh` → `create_nested_treemesh`
- 1D `TensorMesh` → returned unchanged
- 2D `TensorMesh` → `create_nested_2d_tensor`

### Octree nested mesh (`create_nested_treemesh`)

Given the tile's `survey` and the global `base_mesh`, a new `TreeMesh` is
built with the **same cell sizes, origin and extent** as the base mesh, so
the two meshes remain aligned. It is then populated in stages:

1. **Coarse background.** Every base-mesh cell is inserted at a capped
   level `base_level = max_level - minimum_level`. Cells finer than this
   are coarsened, giving a cheap coarse mesh everywhere.
2. **Refinement around receivers** (`_refine_padded_distance`, in 2D).
   Using a `cKDTree` on the tile's unique locations
   (`get_unique_locations`), cells are refined in **concentric shells**:
   for each level `ii` in `range(minimum_level)`, the padding distance
   grows by `base_cell * 2**ii * padding_cells`, and cells within that
   distance are inserted at progressively finer levels (down to the base
   mesh's own level near the data). This preserves the full global
   refinement close to the tile's data and relaxes it with distance.
3. **Source wire paths.** For `LineCurrent` sources (ground/loop TEM and
   FEM), the cells intersected by each transmitter wire
   (`get_intersecting_cells`) are refined too, this time in **3D**, so the
   loop geometry is resolved.
4. `finalize()` completes the tree (unless `finalize=False`).

Parameters:

- `padding_cells` — number of cells per concentric refinement shell.
- `minimum_level` — how many octree levels to peel back outside the local
  survey area (larger ⇒ coarser background ⇒ smaller mesh).

### 2D tensor nested mesh (`create_nested_2d_tensor`)

For draped 2D (DC/IP batch-2D) problems, the nested mesh is a horizontal
slice of the global tensor mesh. The survey's A-electrode X positions are
mapped to mesh columns (`np.searchsorted` on `cell_centers_x`), the unique
`parts` touched are selected, and a `TensorMesh` is rebuilt spanning only
those columns (full vertical extent `h[1]`).

## Step 4 — The local simulation and model mapping (`create_simulation`)

For each tile, `create_simulation` assembles a complete local SimPEG
simulation:

1. **Local survey.** `create_survey` extracts only the sources/receivers
   whose indices belong to the tile (and the requested `channel` for
   frequency systems), copying receivers and slicing `dobs`/`std` and
   `ordering` accordingly.
2. **Local mesh.** If not supplied, `create_nested_mesh` is called
   (default `minimum_level=3`).
3. **Model mapping.**
   - For a `TreeMesh`, a `maps.TileMap(global_mesh, global_active_cells,
     local_mesh, enforce_active=True, components=...)` is created. This is
     the heart of the design: it maps the **global active model** onto the
     **local active cells**. `components=3` is used for vector models /
     remanence; otherwise `1`. `mapping.local_active` gives the tile's
     active-cell mask.
   - For DC/IP 2D (tensor), a `maps.Projection` is built from the global
     active cells to the local active cells by reshaping the active mask
     and selecting the relevant mesh parts.
   - For 1D EM, the "mesh" is the layered `layers_mesh`, and a
     `Projection` extracts the sounding's column from the global model.
4. **Physical property maps.** Depending on which maps the global
   simulation carries, the matching local maps are attached to the local
   active cells: `chiMap` (susceptibility / vector), `rhoMap`
   (resistivity), `sigmaMap` (`ExpMap * InjectActiveCells`), `etaMap`
   (IP chargeability, with background `sigma`), and `remMap`
   (effective-susceptibility remanence, forced to `float32`).
5. **Carry-over settings.** Attributes such as `store_sensitivities`,
   `solver`, `time_steps`, `thicknesses`, etc. are copied from the global
   simulation.
6. **Sensitivity storage.** A deterministic `uuid_from_values` (based on
   mesh size, data count, tile id and simulation type) names the per-tile
   `.zarr` sensitivity file under the global `sensitivity_path`.
7. **Receiver projections.** For EM/DC methods, `compute_em_projections` /
   `compute_dc_projections` rebuild the interpolation from the local mesh
   fields to the receivers.

### From simulation to misfit (`create_misfit` / `_misfit_from_indices`)

`create_misfit` reloads the pickled simulation and builds the local
misfit:

- For most methods, `_misfit_from_indices` builds (optionally) a
  **shared** nested mesh from `shared_indices` once, then a local
  simulation for the specific `indices`, wraps it in a
  `meta.MetaSimulation`, attaches local `dobs`/`std` (unless
  `forward_only`), and returns an `L2DataMisfit`.
- For 1D EM (`BaseEM1DSimulation`), each sounding becomes its own misfit,
  combined into a per-tile `ComboObjectiveFunction`.

## The tile estimator

`simpeg_drivers/utils/tile_estimate.py` (`TileEstimator`) helps pick a
sensible `tile_spatial` before running a full inversion:

- It sweeps candidate tile counts along a **Fibonacci series** (up to
  `max_tiles`).
- For each count it tiles the data, picks the *median-sized* tile, builds
  a local simulation via `create_simulation`, and estimates the total
  problem size in GB as `nD * n_local_active * count * 8 bytes`.
- The **optimal** count is the point of maximum curvature of the
  size-vs-count curve, found by fitting a circle through sliding triplets
  and taking the count with the smallest radius (point of diminishing
  returns).
- It writes a new `SimPEGGroup` with `tile_spatial` set to the optimal
  value and, optionally, a diagnostic plot (size curve + tile map).

## Parameter summary

| Parameter | Where | Effect |
|-----------|-------|--------|
| `tile_spatial` | `compute` options | Number of spatial tiles / clusters. |
| `padding_cells` | driver / nested mesh | Cells per concentric refinement shell around the local survey. |
| `minimum_level` | `create_nested_*mesh` | Octree levels peeled back in the background (coarser ⇒ smaller mesh). |
| `max_chunk_size` | 1D EM | Target sounding chunk size per tile. |
| `n_workers` / workers | driver | Triggers `split_list` sub-splitting (shared mesh) for load balancing. |

## Related files

- `simpeg_drivers/utils/nested.py` — nested mesh, local survey, local
  simulation, misfit builders, `tile_locations`.
- `simpeg_drivers/utils/surveys.py` — `get_unique_locations`,
  `get_intersecting_cells`.
- `simpeg_drivers/driver.py` — `get_tiles`, `split_list`,
  `get_nested_tiles`.
- `simpeg_drivers/electricals/base_2d.py`,
  `simpeg_drivers/electromagnetics/base_1d_driver.py` — method-specific
  tiling.
- `simpeg_drivers/components/factories/misfit_factory.py` — global/
  distributed misfit assembly.
- `simpeg_drivers/utils/tile_estimate.py` — optimal tile-count estimator.
