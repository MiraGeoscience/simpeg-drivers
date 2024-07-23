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
# This section focuses on the inversion of magnetic data using a scalar (susceptibility) and a magnetization (vector) approach generated from the Flin Flon magnetic model ([Figure X](mag_model).
#
# ```{figure} ./images/magnetics/mag_model.png
# ---
# scale: 50%
# name: mag_model
# ---
# ```
#
#
# <p style="page-break-after:always;"></p>

# (magnetic-data)=
#
# ## Forward simulation
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
# For simplicity, the simulation assumes a purely induced response. This is done by omitting to provide values/models for the magnetization inclination and declination. The inducing field parameters are used instead. After running the forward simulation, we obtain RMI data as shown in [Figure X](mag_data). We note the strong correlation between the amplitude of the signal and the horizontal position of the ore body. There is also a significant East-West trend due to the weakly magnetic but large Hidden Formation.
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
# <p style="page-break-after:always;"></p>

# ## Mesh creation
#
# In preparation for the inversion, we create an octree mesh optimized for the magnetic survey. [Figure X]() shows the parameters used.
#
# ```{figure} ./images/magnetics/mesh_core.png
# ---
# scale: 50%
# name: mag_data
# ---
# Residual magnetic intensity (RMI) data measured over the zone of interest.
# ```
#
# For the first refinement, we apply only a couple cells radially around our survey lines to assure that the air-ground interface near the receivers are modeled with the finest cell size.
#
# A second refinement is used along topography to get a coarse but continuous air-ground interface outside the area or interest.
#
# A third "horizon" type of refinement is used to get a core region of increasing cell size with depth directly below the survey.
#
# ```{figure} ./images/magnetics/mesh_refinement.png
# ---
# scale: 50%
# name: mag_refinement
# ---
# Refinement strategy used for the magnetic modeling.
# ```
#
# See [Mesh creation](../inversion/mesh_design.ipynb) section for general details on the parameters.
#

# ## Scalar inversion (susceptibility)
#
# **Runtime: ~1 min**
#
# As a first pass, we invert the data with default parameters shown in [Figure X](data_input). We use a constant 25 nT floor uncertainty, determined empirically to achieve good fit.
#
# ```{figure} ./images/data_input.png
# ---
# height: 400px
#
# name: mag_default
# ---
# (Top) (left) Observed and (right) predicted data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models.
# ```
#
# Following the smooth solution, a series of IRLS iterations were performed to recover an alternate, more compact model. The following figure shows sections through the recovered models and compares the observed and predicted data.
#
#
# ```{figure} ./images/data_input.png
# ---
# height: 400px
#
# name: mag_default
# ---
# (Top) (left) Observed and (right) predicted data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models.
# ```
#
#
# ### No reference model
#
# From our previous attempt, we note that large portions of the model, in the padding cells and at depth, have no anomalies. All the magnetic signal is confined to a region directly below the survey lines. This is somewhat surprising given the large East-West trend in the data, which would be better explain by a large body extending beyond the extent of our survey.
# As a second pass, we test whether our initial assumption of a uniform 0 susceptibility model is adequate ([Figure X]())
#
# The recovered model shown in [Figure X](data_input) generally agrees with the position of the strongly magnetic ore body, but changes greatly outside the survey area. Since we have not imposed any constraints on the background value, the inversion is free to extend the anomaly both at depth and in the padding region.
#
#
# [To be continued with detrending and regional removal]

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
