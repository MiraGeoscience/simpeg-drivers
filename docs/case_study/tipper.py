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
# This section focuses on the inversion of airborne tipper data.
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
