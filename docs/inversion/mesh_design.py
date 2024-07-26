# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # Mesh design
#
# This section provides details about the mesh creation towards joint inversions. The goal is to create inversion meshes that are well adapted to each survey, while also optimal for the subsequent joint inversion process.
#
# For further details and examples on how to create octree meshes, please visit the [Octree Mesh Creation](https://mirageoscience-octree-creation-app.readthedocs-hosted.com/en/latest) documentation provided by [Mira Geoscience](https://www.mirageoscience.com/mining-industry-software/python-integration).
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
# Since we need our three simulations (direct-current, magnetics and gravity) to have the same core parameters, we need to create a  "combined" survey that contains all source and receiver locations in our domain.
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
# Numerical artefacts due to the discretization of topography decay sufficiently when receivers are roughly two cell dimensions away from the nearest edge or corner. Since the lowest drape height from the airborne magnetics is 60 m, a prudent cell size would be in the range of ~30 m.  We also want to avoid computing electrical potential differences within the same cell for numerical accuracy.  This is condition is guaranteed for cell dimensions less than half the smallest dipole separation - suggesting an even smaller cell (<=20 m) dimension for the 40m dipole direct-current data simulated here.
#
#
# ### Padding cells
#
# The area of interest covers roughly 2 km in width. As a general rule of thumb, the padding region should be at least as wide as the data extent in order to easily model features with wavelengths that may extend beyond the surveyed area.
#
# (diffusion-distance)=
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
# $$
# \delta = \sqrt{\frac{2t \; \rho}{\mu_0}}
# $$
#
# where $t$ is the largest time measured by the system and $\mu_0$ is the permeability of free space ($4 \pi * 1e-7$).
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
# An octree mesh allows to increase the mesh resolution (smaller cells) in specific regions - warranted for either numerical accuracy or modeling purposes. Fine cells can be "added" to the octree grid using various insertion methods that depend on the type of object used:
#
# - Radial: Add concentric spherical shells of cells around points. It is the default behaviour for `Points`-like objects.
# - Line: Add concentric tubes around line segments. It is the default discretization for line sources (EM loops) and `Curve` objects.
# - Surface: Add layers of cells along triangulated surfaces in 3D. It is the default behaviour for `Surface` objects and mostly used to refine known boundaries between geological domain and topography.
# - Horizon [Optional]: Add horizontal layers of cells below a triangulated surface computed from the input object's vertices. This is a useful option to create a core region below the survey area.
#
# See the [Octree-Creation-App: Refinements](https://mirageoscience-octree-creation-app.readthedocs-hosted.com/en/latest/methodology.html#refinements) section for more details.
#
#
#
# ### For direct-current survey
#
# For EM methods, such as electrical direct-current surveys, the numerical accuracy of the forward simulation is the primary  factor to decide on a mesh refinement strategy. It is important to have several small cells around each source and receivers for solving partial differential equations accurately. In this case, dipole source and receivers must be converted to a `Points` object in order to trigger a `radial` refinement. Concentric shells of cells are added around each source/receiver poles.
#
# ```{figure} ./images/mesh_dc.png
# ---
# scale: 50%
# name: mesh_dc
# ---
# Parameters used for the mesh creation of the direct-current simulation.
# ```
#
# A second level of `Surface` refinement was added along the triangulated topography. Only coarse cells (3th octree level) were needed to preserve good continuity of the fields near the boundary of the domain.
#
#
# ### For gravity and magnetic surveys
#
#
# For potential field methods, the forward simulation is achieved via integration over prisms (linear operator) which is much less sensitive to the choice of discretization. Moreover, only cells below topography (active cells) are considered. For a more optimal mesh design, only fine cells are required at the air-ground interface. A `horizon` style refinement was used in order to add layers of fine cells below the footprint of the gravity and magnetic sensors. The maximum `distance` parameter was set to 100 m to reduce the number of small cells away from the receiver locations.
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
