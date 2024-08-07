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
# # Airborne Tipper Inversion
#
#
# This section focuses on the inversion of airborne tipper data generated from the Flin Flon resistivity model.
#
# ```{figure} ./images/tipper/tipper_model.png
# ---
# scale: 25%
#
# name: dc_model
# ---
# [Download here](https://github.com/MiraGeoscience/simpeg-drivers/blob/develop/simpeg_drivers-assets/inversion_demo.geoh5)
# ```
#
# ```{note}
# Runtime and memory usage increases rapidly with the mesh size and number of sources (frequencies). It is strongly recommended to downsize this example to a few lines if the training is done on a standard computer. The full inversion presented below was performed on an Azure HC44rs node (44 CPUs, 315 Gb RAM) in ~2.0 h.
# ```
#
# <p style="page-break-after:always;"></p>

# (tipper-data)=
#
# ## Airborne tipper (Natural Source EM)
#
# We generated an airborne tipper survey over the main ore body. The survey lines are spaced at 400 m, oriented East-West, at a drape height of 60 m.
#
# Tipper systems collect three orthogonal components of the ambient magnetic field ($H_x,\;H_y,\;H_z$). Similar to magnetotelluric surveys, the ratios of the components are used to circumvent the unknown source of the EM signal. The transfer functions, or tipper, are calculated by taking the ratio of the fields for two polarizations of the magnetic fields (EW and NS). The measurements are generally provided in the frequency-domain with both a real and an imaginary component. For more background information about natural source methods, see [em.geosci](https://em.geosci.xyz/content/geophysical_surveys/ztem/index.html)
#
#
# ```{figure} ./images/tipper/tipper_forward.png
# ---
# scale: 50%
# name: tipper_forward
# ---
# ```
#
# The survey used here mimics the commercial [ZTEM](https://geotech.ca/services/electromagnetic/ztem-z-axis-tipper-electromagnetic-system/) system that measures the vertical magnetic field ($H_z$) on a towed platform at 6 frequencies (30, 45, 90, 180, 360 and 720 Hz). The horizontal fields ($H_x,y$) are measured at a fixed base station located in the center of the survey area.
#
# ```{figure} ./images/tipper/tipper_data.png
# ---
# scale: 50%
# name: tipper_topo
# ---
# (Top) Tipper data displayed by the 2D Profiler at all 6 frequencies for the 4 components ($T_{zx}$, $T_{zy}$, real and imaginary). (Bottom) Survey lines relative to (left) the ore body and (right) the discrete conductivity model.
# ```
#
# Note that the position of the known conductor correlates with large gradients in the tipper data.
#
# <p style="page-break-after:always;"></p>

# ## Mesh creation
#
# In preparation for the inversion, we create an octree mesh optimized for the tipper survey.  The mesh parameters are base on the original Flin Flon model.
#
# ```{figure} ./images/tipper/tipper_core.png
# ---
# scale: 50%
# name: tipper_core
# ---
# Core mesh parameters.
# ```
#
# Note that the padding distances are set substantially further than for the magnetics, gravity or dc-resistivity (1 km) inversions. This is because the [diffusion distance](diffusion-distance) for a background resistivity of $1000 \; \Omega .m$ for the lowest frequency (30 Hz) is roughly 3 km. This distance is important to satisfy the [boundary conditions](https://em.geosci.xyz/content/maxwell1_fundamentals/solving_maxwells_equations.html?highlight=boundary%20conditions#boundary-and-initial-conditions) of the underlying differential equations.
#
#
# ### Refinements
#
# - For the first refinement, we insert 4 cells for the first three octree levels along the flight path. The refinement is done radially around the segments of the flight path curve to assure good numerical accuracy near the receiver locations. This is especially important for EM methods with low frequencies.
#
# - We use a second refinement along topography to get a coarse but continuous air-ground interface outside the area or interest.
#
# - Lastly, we refine a "horizon" get a core region at depth with increasing cell size directly below the survey. This is our volume of interest most strongly influenced by the data.
#
# ```{figure} ./images/tipper/tipper_refinement.png
# ---
# scale: 50%
# name: tipper_refinement
# ---
# Refinement strategy used for the tipper modeling.
# ```
#
# See [Mesh creation](../inversion/mesh_design.ipynb) section for general details on the parameters.


# ## Unconstrained inversion
#
# **Runtime: ~2.0 h**
#
# Tipper data involves 2 receiver configuration (x and y), with two components (real and imaginary) and measured over 6 frequencies. Balancing all this data can be challenging and time consuming. Here we adopt a variable floor strategy based on the 10th percentile of each data layer.
#
# ```{figure} ./images/tipper/tipper_uncerts.png
# ---
# scale: 50%
# name: tipper_uncerts
# ---
# ```
#
# This approach is a good starting point, but experimentation is generally required.
#
# After running the inversion we recover the following solution:
#
#
# ```{figure} ./images/tipper/tipper_unconstrained.png
# ---
# name: tipper_unconstrained
# ---
# (Left) Horizontal section at 120 m elevation after reaching target misfit (iteration 5).
#
# (Right)(top) 2D profiles of observed versus predicted data for all 4 channels and 6 frequencies and (bottom) vertical section through the conductivity model below the same line.
# ```
#
# Despite our simplistic floor uncertainties, the inversion managed to converge fairly quickly to a reasonable model that fits our data well. We have recovered a clear conductor at depth that overlaps with ore body. The inversion could not however resolve the thin conductive overburden layer, as expected by the low frequency range of the tipper system.
