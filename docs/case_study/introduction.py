# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# <p style="page-break-after:always;"></p>
#
# # Tutorials
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
#
# This chapter demonstrates how to run standalone and joint inversions of geophysical data using SimPEG and the user-interface created for Geoscience ANALYST. We generated several synthetic surveys over the Flin Flon model to simulate an exploration program over a VMS deposit.
# The goal is to use ground and airborne geophysics to characterize the physical property and shape of the ore body and host rocks. This case study focuses on the following three datasets and respective physical properties:
#
# - [Direct-current resistivity (DCR)](dc-data) -> resistivity
# - [Magnetic Total Field (TMI)](magnetic-data) -> magnetization
# - [Full-tensor gravity gradiometry (FTG)](ftg-data) -> density
#
# The datasets are first inverted independently ([Figure 1](standalone)), then jointly with a cross-gradient coupling constraint ([Figure 2](joint)).
#
# The following sections provide details about the processing and results. A compilation `geoh5` project can be found in the `simpeg-drivers-assets` folder.
#
# - [Background information](background.ipynb)
# - [Data](data.ipynb)
# - [Mesh design](mesh_design.ipynb)
# - [Unconstrained inversions](unconstrained_inversion.ipynb)
# - [Joint inversion](joint_inversion.ipynb)
