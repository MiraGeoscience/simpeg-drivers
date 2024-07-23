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
# # Magnetic Inversion
#
# This section focuses on the inversion of magnetic data using a scalar (susceptibility) and a magnetization (vector) approach.
#
#
# <p style="page-break-after:always;"></p>

# (magnetic-data)=
#
# ## Data (TMI)
#
# We simulated Residual Magnetic Intensity (RMI) data along East-West lines at a 40 m drape height above topography. The line spacing was set to 200 m, with along-line data downsampled to 10 m.
#
# The following parameters were used for the forward simulation:
#
# ```{figure} ./images/magnetics/forward.png
# ---
# scale: 50%
# name: mag_forward
# ---
# ```
#
# This simulation assumes a purely induced response with no additional information provided about the direction of magnetization.
#
#
#
# ```{figure} ./images/magnetics/MAG_data.png
# ---
# scale: 50%
# name: mag_data
# ---
# Residual magnetic intensity (RMI) data measured over the zone of interest.
# ```
#
# We can notice a strong correlation between the RMI data and the horizontal position of the ore body.
#
# <p style="page-break-after:always;"></p>

# ## Mesh creation
#
# In preparation for the the inversion, we can create an optimal octree mesh for this survey. For potential fields data, only the discretization below ground matters as air cells are ignored in the calculations. [Figure X]() shows the parameters used in this case.
#
# ```{figure} ./images/magnetics/mesh_core.png
# ---
# scale: 50%
# name: mag_data
# ---
# Residual magnetic intensity (RMI) data measured over the zone of interest.
# ```
#
# For the refinement, ...
#
#
# ```{figure} ./images/magnetics/mesh_refinement.png
# ---
# scale: 50%
# name: mag_data
# ---
# Residual magnetic intensity (RMI) data measured over the zone of interest.
# ```
#
#
# See [Mesh creation](../inversion/mesh_design.ipynb) section for general details on the parameters.
#

# ## Scalar inversion (susceptibility)
#
# The airborne magnetic data were inverted over a range of uncertainties in order to achieve an adequate data fit. Following the smooth solution, a series of IRLS iterations were performed to recover an alternate, more compact model. The following figure shows sections through the recovered models and compares the observed and predicted data.
#
#
# ```{figure} ./images/mag_model_TOP.png
# ---
# height: 400px
#
# name: mag_model_TOP
# ---
# (Top) (left) Observed and (right) predicted data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models.
# ```
#

# ## Magnetic vector inversion (MVI)
#
# The airborne magnetic data were inverted over a range of uncertainties in order to achieve an adequate data fit. Following the smooth solution, a series of IRLS iterations were performed to recover an alternate, more compact model. The following figure shows sections through the recovered models and compares the observed and predicted data.
#
#
# ```{figure} ./images/mag_model_TOP.png
# ---
# height: 400px
# name: mag_model_TOP
# ---
# (Top) (left) Observed and (right) predicted data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models.
# ```
#
#
# [Add more here]
#
#
# <p style="page-break-after:always;"></p>

# ## Compact models
#
#
#
