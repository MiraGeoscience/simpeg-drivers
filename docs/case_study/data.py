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
# # Data
#
# This section provides details about the three airborne datasets used in this case study:
#
# - [Time-domain EM (HeliTEM)](atem-data)
# - [Magnetic total field (HeliTEM)](magnetic-data)
# - [Airborne full-tensor gravity gradiometry (FTG)](ftg-data)
#
# Initial datasets provided to Mira covered a large region of approximately $275km^2$ with good overlap between the three blocks. After preliminary analysis, the decision was made to focus the work on the southern portion of Block 3 as shown in [Figure 5](project_area). The area of focus was chosen based on:
#
#  - Overlap with a known but under-explored iron-deposit
#
#  -  Manageable size for processing speed.
#
#  - Limited cultural noise from mine infrastructure nearby.
#
#
#
# ```{figure} ./images/project_area.png
# ---
# scale: 50%
# name: project_area
# ---
# Data coverage from the Helitem survey (black) over the zone of interest. Only a subset (red) of the survey was used for the time-domain inversion.
# ```
#
# <p style="page-break-after:always;"></p>

# (atem-data)=
#
# ## Airborne time-domain EM (TEM)
#
# An airborne time-domain survey was flown by Xcalibur in late November 2022 over the Carajas region. The survey was flown mostly with parallel lines in the North-South direction spaced 100 m at a nominal clearance of 109 m above ground. East-West tie lines were flown with a spacing of 1 km ([Figure 6](helitem_topo)).
#
# ```{figure} ./images/Helitem_topo.png
# ---
# scale: 50%
# name: helitem_topo
# ---
# Helitem survey flight lines over Carajas-Block 3 and topography from the SRTM elevation model.
# ```
#
# Given the presence of negative transients over a large portion of the survey, only the 15 first time channels were used for modeling ([Figure 7](helitem_data)).
#
#
#
# ```{figure} ./images/Helitem_data.png
# ---
# scale: 50%
# name: helitem_data
# ---
# North-South data profile from the Helitem survey over the known mineralization and mining infrastructure.
# ```
#
# The theoretical waveform of the Helitem system was approximated by a semi-rectangular pulse with an 8 msec on-time and 3 msec ramp-off.
#
# ```{figure} ./images/Helitem_waveform.png
# ---
# height: 400px
# name: helitem_waveform
# ---
# Idealized waveform used for time-domain modeling.
# ```
#
# <p style="page-break-after:always;"></p>

# (magnetic-data)=
#
# ## Airborne magnetic survey (MAG)
#
# Alongside the EM sensor, the HeliTEM system carries a Scintrex Cesium vapour magnetometer that measures total magnetic field intensity (TMI) as shown below.
#
# ```{figure} ./images/MAG_data.png
# ---
# scale: 50%
# name: mag_data
# ---
# Residual magnetic intensity (RMI) data measured over the zone of interest.
# ```
#
#
# Xcalibur applied a series of corrections and leveling routines on the data to account for diurnal variations, lag and altitude variations. We did not use the altitude corrected data for the inversion in order to preserve the natural fluxations in intensity with respect to distance from the source, which is handled by the physics of the forward simulation. The following inducing field parameters were used for the residual data and modeling:
#
# | Intensity | Declination | Inclination |
# | :--- | :--- | :---- |
# | $24950$ nT |   $-20.65^\circ$   | $-12.39^\circ$ |
#
# <p style="page-break-after:always;"></p>

# (ftg-data)=
#
# ## Airborne full-tensor gravity gradiometry (FTG)
#
# An airborne fixed-wing full-tensor gravity gradiometry (FTG) survey was flown by Bell Geospace between July and October 2005 over the same area at a 150 m line separation, 100 m nominal flight height.
#
# The FTG system measures six independent components of the gradient tensor: Txx, Txy, Txz, Tyy, Tyz and Tzz. Data were leveled, free-air and terrain corrected (2.67 g/cc) by the contractor. No additional processing was performed by Mira other than downsampling to 50 m along line.
#
#
# ```{figure} ./images/FTG_data.png
# ---
# scale: 50%
# name: ftg_data
# ---
# Components of the gravity gradiometry data measured over the zone of interest (from to bottom): (left) Txx, Tyy and Tzz components, (right) Tyx, Txz and Tyz components.
# ```
#
