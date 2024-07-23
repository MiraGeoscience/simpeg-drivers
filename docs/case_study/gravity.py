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
# # Gravity Inversion
#
# This section focuses on the inversion of airborne tensor and ground gravity data.
#
#
#
# <p style="page-break-after:always;"></p>

# ## Ground gravity data
#
#
# A ground gravity survey was simulated on sparsely sampled 200 m grid of stations. The data are provided a terrain corrected with
# reference density of 2.67 g/cc.
#
# ```{figure} ./images/GZ_data.png
# ---
# scale: 50%
# name: gz_data
# ---
# Vertical component of the gravity field (gz) measured over the zone of interest.
# ```
#

# ## Unconstrained ground gravity
#
# The ground gravity data (terrain corrected at 2.67 g/cc) were also inverted in the same fashion. A floor uncertainty value of 0.05 mGal was assigned.
#
#
#
# ```{figure} ./images/ground_grav_model_TOP.png
# ---
# height: 400px
# name: ground_grav_model_TOP
# ---
# (Top) (left) Observed and (right) predicted gz data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice for (left) the smooth and (right) L1-norm density contrast models.
# ```
#
# [Add more here]
#
# We note a slight correlation to the shape of the known ore body
#

# (ftg-data)=
#
# ## Tensor gravity gradiometry (FTG)
#
# An airborne fixed-wing full-tensor gravity gradiometry (FTG) survey was simulated at a nominal drape height of 60 m above topography.
#
# The FTG system measures six independent components of the gradient tensor: $g_{xx},\; g_{xy},\; g_{xz},\; g_{yy},\; g_{yz}$ and $g_{zz}$. Data were leveled, free-air and terrain corrected with 2.67 g/cc reference density.
#
#
# ```{figure} ./images/GG_data.png
# ---
# scale: 50%
# name: ftg_data
# ---
# (Top) Components of the gravity gradiometry data measured over the zone of interest. (Bottom) The green and red marker indicate the flight direction.
# ```
#

# ## Unconstrained FTG
#
# The airborne tensor gravity data (terrain corrected at 2.67 g/cc) were also inverted in the same fashion. A floor uncertainty value of 0.2 Eotvos was assigned to all the components.
#
#
#
# ```{figure} ./images/grav_gradio_model_TOP.png
# ---
# height: 400px
# name: grav_gradio_model_TOP
# ---
# (Top) (left) Observed and (right) predicted gxx data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice for (left) the smooth and (right) L1-norm density contrast models.
# ```
#
# We note a slight correlation to the shape of the known ore body
#
#
# <p style="page-break-after:always;"></p>
