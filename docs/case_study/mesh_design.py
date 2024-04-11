# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # Mesh design
#
# This section provides details about the mesh creation for the individual inversions using the `Octree Mesh Creation` routine from [Mirageoscience\geoapps](https://geoapps.readthedocs.io/en/latest/content/applications/create_octree.html) package. The goal is to create inversion meshes that are well adapted to each survey, while also optimal for the subsequent joint inversion process.
#
#
# ## Base parameters
#
# In a first step, we need to decide on
#
# - [A region of interest (extent)](#Mesh-extent)
# - [Base cell resolution](#Base-cell-size)
# - [Padding distance](#Padding-cells)
#
# These parameters define our core mesh parameters. While each survey can have its own discretization (refinements), the joint inversion routine requires all meshes to have the same outer extent and base cell size. The following sections provide details on the choices made.
#
#
# ### Mesh extent
#
# Since we need our three simulations (TEM, magnetics and gravity) to have the same core parameters, we need to create a  "combined" survey that contains all source and receiver locations in our domain.
#
#
# ```{figure} ./images/common_survey.png
# ---
# scale: 50%
# name: common_survey
# ---
# Creation of a combined curve object from all surveys.
# ```
#
# ### Base cell size
#
# Next, we need to define a base cell size for the core region. A few criteria need to be taken into consideration:
#
# - Sources/receivers separation
# - Terrain clearance (height above ground)
# - Modeling resolution (size of the target)
#
# In this case, the flight clearance of both the airborne EM/mag and FTG had a minimum recorded clearance of about 80 m. As a general rule of thumb, numerical artefacts due to the discretization of topography decays sufficiently when roughly two cell distance away from the nearest edge or corner. The choice was made to invert at a 25 m cell resolution to assure at least 2 cells between the lowest point and the discrete active model.
#
#
# ### Padding cells
#
# The area of interest covers roughly 5 km by 8 km. As a general rule of thumb, the padding region should be at least as wide as the data extent in order to easy model features with wavelengths that may extend beyond the surveyed area.
#
# In the case of EM modeling, we also need to consider the diffusion distance of the EM fields. The [skin depth](http://em.geosci.xyz/content/maxwell1_fundamentals/harmonic_planewaves_homogeneous/skindepth.html?highlight=skin%20depth#approximations) can be estimated by
#
# $$
# \delta = 503 \sqrt{\frac{\rho}{f}}
# $$
#
# where $\rho$ is the expected resistivity of the background and $f$ is the base frequency of the system.
#
# Equivalently for time-domain systems
#
#
#
# $$
# \delta = \sqrt{\frac{2t \; \rho}{\mu_0}}
# $$
#
# where $t$ is the largest time measured by the system and $\mu_0$ is the permeability of free space ($4 \pi * 1e-7$). For a Helitem survey, with the last time gate at 7.1 msec, and moderately resistive ground (~1000 Ohm.m), the skin depth is roughly 3.3 km. This number was rounded up to the next power of 2 (2^N) to satisfy the octree structure, resulting in roughly 6 km of padding at depth.
#
#
#
# ```{figure} ./images/mesh_core.png
# ---
# scale: 50%
#
# name: mesh_core
# ---
# Core parameters used for the mesh creation of each inversion. Only the refinement strategies differ between surveys.
# ```

# ## Refinements
#
# An octree mesh allows to increase the mesh resolution (smaller cells) in specific regions - warranted for either numerical accuracy or modeling purposes. Fine cells can be "added" to the octree grid using various insertion methods:
#
# - Ball: Add concentric spherical shells of cells around points: Mostly used for numerical accuracy near receivers.
# - Line: Add concentric tubes around line segments: Mostly used to discretize line sources (EM loops)
# - Surface: Add layers of cells along triangulated surfaces: Used to refine known boundaries between geological domain and topography
# - Box: Add rectangular boxes of cells around extent: Simple refinement resembling conventional rectilinar (tensor) grids.
#
#
#
# ### For time-domain EM
#
# For airborne EM surveys, the numerical accuracy of the forward simulation is the driving factor for the mesh refinement. It is important to have several small cells around each source and receivers for solving partial differential equations. The radial `ball` refinement was used to add concentric layers of cells around each source/receiver pairs.
#
# ```{figure} ./images/mesh_em.png
# ---
# scale: 50%
# name: mesh_em
# ---
# Parameters used for the mesh creation of the EM simulation.
# ```
#
# A second level of `surface` refinement was added along the topography. Only coarse cells (4th octree level) were needed to preserve good continuity of the fields near the boundary of the domain.
#
#
# ### For gravity and magnetics
#
#
# For potential field methods, the forward simulation is achieved via integration over prisms (linear operator) which is much less sensitive to the choice of discretization. Moreover, only cells below topography (active cells) are considered. For a more optimal mesh design, only fine cells are required at the air-ground interface. A `surface` style refinement was used in order to add layers of fine cells below the footprint of the gravity and magnetic sensors as well as coarser (octree level 4) cells at the air-ground interface away from the sensors
#
# ```{figure} ./images/mesh_mag.png
# ---
# scale: 50%
# name: mesh_mag
#
# ---
# Parameters used for the mesh creation of the EM simulation.
# ```
#
