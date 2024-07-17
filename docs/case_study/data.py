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
# # Data
#
# This section provides details about the various datasets simulated for this tutorial:
#
# - [Magnetic total field (HeliTEM)](magnetic-data)
# - [Airborne full-tensor gravity gradiometry (FTG)](ftg-data)
# - [Direct-current resistivity (DCR)](dc-data)
# - [Airborne Tipper (NSEM)](tipper-data)
#
#
# ```{figure} ./images/project_area.png
# ---
# scale: 50%
# name: project_area
# ---
# Data coverage for the ground gravity (black), airborne gravity gradiometry (red), airborne magnetics (green) and direct-current (blue) surveys. Outline of the ore shell (gray) is shown for reference.
# ```
#
# <p style="page-break-after:always;"></p>

# (magnetic-data)=
#
# ## Airborne magnetic survey (TMI)
#
# We simulated Residual Magnetic Intensity (RMI) data along East-West lines at a 40 m drape height above topography. The line spacing was set to 200 m, with along-line data downsampled to 10 m.
#
# The following inducing field parameters were used for the forward simulation:
#
# | Intensity | Declination | Inclination |
# | :--- | :--- | :---- |
# | $60000$ nT |   $11^\circ$   | $79^\circ$ |
#
#
# ```{figure} ./images/MAG_data.png
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

# (ftg-data)=
#
# ## Airborne tensor gravity gradiometry (FTG)
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

# ## Ground gravity survey
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

# (dc-data)=
#
# ## Direct-current resistivity (DCR)
#
# A ground dipole-dipole survey was simulated over the main ore body. The survey was acquired with 40 m dipole length, data measured on seven receivers per transmitter dipole. Line separation was set to 100 m ([Figure 5](dc_topo)).
#
# ```{figure} ./images/DCR_data.png
# ---
# scale: 50%
# name: dc_topo
# ---
# Pseudo-sections of apparent resisitvity and topography from the SRTM elevation model.
# ```
#
# Note the large contrast in apparent resistivity between the western and eastern regions of the survey. This can be explained by a conductive tailing layer West of the deposit.
#
# <p style="page-break-after:always;"></p>

# (tipper-data)=
#
# ## Airborne tipper (Natural Source EM)
#
# An airborne tipper survey was simulated over the main ore body. The survey was acquired along East-West lines, 400 m spacing, at a drape height of 60 m ([Figure 5](dc_topo)).
# Tipper systems collect three orthogonal components of the ambiant magnetic field ($H_x,\;H_y,\;H_z$) in time. Similar to magnetotelluric surveys, the ratios of the components are used to circumvent the unknown source of the EM signal. The transfer functions, or tipper, are calculated by taking the ratio of the fields for two polarizations of the magnetic fields (EW and NS). The measurements are generally provided in the frequency-domain with both a real and an imaginary component.
# For more background information about natural source methods, see [em.geosci](https://em.geosci.xyz/content/geophysical_surveys/ztem/index.html)
#
# The survey used in this tutorial mimics the commercial [ZTEM](https://geotech.ca/services/electromagnetic/ztem-z-axis-tipper-electromagnetic-system/) system that measures the magnetic field at 6 frequencies (30, 45, 90, 180, 360 and 720 Hz). The base station is located at the center of the survey area.
#
# ```{figure} ./images/tipper_data.png
# ---
# scale: 50%
# name: tipper_topo
# ---
# Tipper data displayed by the 2D Profiler at all 6 frequencies for the 4 components ($T_{zx}$, $T_{zy}$, real and imaginary).
# ```
#
# Note that the position of the known conductor correlate with large variations in the tipper data.
#
# <p style="page-break-after:always;"></p>
