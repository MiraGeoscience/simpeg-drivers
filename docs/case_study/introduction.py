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
# # Tutorials
#
# This chapter demonstrates how to run standalone and joint inversions of geophysical data using SimPEG and the user-interface created for Geoscience ANALYST. We generated several synthetic surveys over the Flin Flon model to simulate an exploration program over a VMS deposit.
# The goal is to use ground and airborne geophysics to characterize the physical property and shape of the ore body and host rocks. This case study focuses on the following three datasets and respective physical properties:
#
# In preparation for the joint inversion, we first inverted each dataset independently ([Figure 1](standalone)). It serves as a quality control step for data uncertainties estimation and mesh design. We can solve possible convergence issues before attempting to couple the physical property models in a joint process.
#
# The data is then jointly with a cross-gradient coupling constraint ([Figure 2](joint)).
#
#
# ```{figure} ./images/ore_body.png
# ---
# height: 400px
# name: ore_body
# ---
# Discrete geological model of the ore deposit and host units.
# ```
#
# The following sections provide details about the processing and results. A compilation `geoh5` project can be found in the `simpeg-drivers-assets` folder or [download here](https://github.com/MiraGeoscience/simpeg-drivers/raw/develop/simpeg_drivers-assets/inversion_demo.geoh5?download=).
#
# - [Background information](background.ipynb)
# - [Magnetic Total Field (TMI)](magnetic)
# - [Full-tensor gravity gradiometry (FTG)](gravity)
# - [Direct-current resistivity (DCR)](dc_resistivity)
# - [Airborne Tipper (NSEM)](tipper)
# - [Airborne Time-Domain EM (ATEM)](airborne_tem)
# - [Joint inversion](joint_inversion.ipynb)
