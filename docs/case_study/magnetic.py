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
# This section focuses on the inversion of magnetic data using a scalar (susceptibility) and a magnetization (vector) approach generated from the Flin Flon magnetic model. We also cover some strategies on how to remove regional signal and the use of compact norms.
#
#
#
# ```{figure} ./images/magnetics/mag_model.png
# ---
# scale: 25%
#
# name: mag_model
# ---
# [Download here](https://github.com/MiraGeoscience/simpeg-drivers/blob/develop/simpeg_drivers-assets/inversion_demo.geoh5)
# ```
#
#
# <p style="page-break-after:always;"></p>

# (magnetic-data)=
#
# ## Forward simulation
#
# We simulated Residual Magnetic Intensity (RMI) data along East-West lines spaced to 200 m apart, with along-line data downsampled to 10 m. The flight height is set to 40 m above topography.
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
# For simplicity, the simulation assumes a purely induced response. By omitting to supply values/models for the inclination and declination of magnetization, the forward routine uses the inducing field parameters instead.
#
# After running the forward simulation, we obtain RMI data as shown in [Figure 9](mag_data). We note the strong correlation between the amplitude of the signal and the horizontal position of the ore body. There is also a significant long wavelength East-West trend, due to the large but weakly magnetic Hidden Formation.
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
# In preparation for the inversion, we create an octree mesh optimized for the magnetic survey. [Figure 10](mag_core) shows the parameters used.
#
# ```{figure} ./images/magnetics/mesh_core.png
# ---
# scale: 50%
# name: mag_core
# ---
# Core mesh parameters.
# ```
#
# - For the first refinement, we insert two cells around our survey lines. The refinement is done radially around the segments of the curve to assure that the air-ground interface near the receivers are modeled with the finest cell size.
#
# - A second refinement is used along topography to get a coarse but continuous air-ground interface outside the area or interest.
#
# - The third refinement "horizon" is used to get a core region at depth with increasing cell size directly below the survey. This is our volume of interest most strongly influence by the data.
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
# As a first pass, we invert the data with default parameters shown in [Figure 12](mag_default). We use a constant 25 nT floor uncertainty, determined empirically to achieve good fit. After running the inversion we obtain:
#
# ```{figure} ./images/magnetics/mag_model_default.png
# ---
# name: mag_default
# ---
# (Top) (left) Predicted and (right) residuals data after reaching target misfit (iteration 3).
#
# (Bottom) Slices through the recovered susceptibility model: (left) at 175 m elevation and (right) at 6072150 m N.
# ```
#
# We note that our model predicts the data within our uncertainty floor of 25 nT. In plan view, the model shows a clear North-West trend corresponding to the ore body. On the vertical section we recover an isolate body at depth. We note that large portions of the model in the padding cells have no anomalies. All the magnetic signal is confined to a region directly below the survey lines. This is somewhat surprising given the large East-West trend in the data, which would be better explain by a large body extending beyond the extent of our survey.
#
#
# ### No reference model
#
# As a second pass, we test whether our initial assumption of a uniform zero susceptibility model is adequate. We can remove the influence on the reference model by setting the corresponding scaling factor to 0. After re-running the inversion we recover:
#
# ```{figure} ./images/magnetics/no_ref_input.png
# ---
# scale: 50%
# name: no_ref_input
# ```
#
# The model shown in [Figure 13](mag_no_ref) generally agrees with the position of the strongly magnetic ore body, but changes greatly outside the survey area. Since we have not imposed any constraints on the background value, the inversion is free to extend the smoothout the eastern anomaly both at depth and in the padding region. This is in better agreement with our known geological knowledge.
#
#
# ```{figure} ./images/magnetics/mag_model_no_ref.png
# ---
# name: mag_no_ref
# ---
# (Top) (left) Predicted and (right) residuals data after reaching target misfit (iteration 3).
#
# (Bottom) Slices through the recovered susceptibility model: (left) at 175 m elevation and (right) at 6072150 m N.
# ```
#

# ## Magnetic vector inversion (MVI)
#
# We now look at the solution using the magnetic vector inversion (MVI) algorithm. This approach is generally favoured if [remanent magnetization](https://gpg.geosci.xyz/content/magnetics/magnetics_basic_principles.html?highlight=remanence#remanent-magnetization) is kwown to distorte the magnetic signal.
#
# We use the default parameters but without a reference model as shown below.
#
# ```{figure} ./images/magnetics/mvi_input.png
# ---
# scale: 50%
# name: mvi_input
# ```
#
# After running the inversion, we obtain
#
#
# ```{figure} ./images/magnetics/mvi_model.png
# ---
# name: mvi_model
# ---
# (Top) (left) Predicted and (right) residuals data after reaching target misfit (iteration 3).
#
# (Bottom) Slices through the recovered susceptibility model: (left) at 175 m elevation and (right) at 6072150 m N.
# ```
#
# We note that the effective susceptibility values are much lower than recovered with the scalar susceptibility inversion. The anomaly is also smoother, broader and less well defined at depth. This can be explained by the increase in non-uniquess of the inverse problem, where we now have to solve for three models (vectors) at once. This result could be improved with additional constraints, but beyond the scopy of this section.
#
#
# ### Algorithmic details
#
# Looking back at the log file, users may notive that the MVI process goes through three main stages:
#
# 1- Solve the problem in Cartesian (3-components) form for a smooth model
#
# 2- Convert the model to Spherical (amplitude and angles) and iterate to target misfit.
#
# 3- Use the smooth Spherical model for the compact IRLS iterations.
#
# ```{figure} ./images/magnetics/mvi_log.png
# ---
# scale: 50%
# name: mvi_log
# ```
#
# Note that the last Cartesian model ends after reaching a target misfit of about 2x (hard-coded). User should preferentially use the last model from the Spherical steps, or last of IRLS, to do their interpration as both are on or near target.
#
# See [Fournier et al. 2020](https://owncloud.eoas.ubc.ca/s/iXrwgjXjierfoKa/download) for more details.
#
# <p style="page-break-after:always;"></p>
