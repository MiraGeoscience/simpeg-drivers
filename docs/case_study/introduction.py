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
# # Case Studies
#
#
# ```{figure} ./images/standalone_10clusters.png
# ---
# scale: 50%
# align: right
# name: standalone
# ---
# Standalone physical property model.
# ```
#
#
# ```{figure} ./images/joint_10clusters.png
# ---
# scale: 50%
# align: right
# name: joint
# ---
# Joint physical property model.
# ```
#
#
# This chapter demonstrates standalone and joint inversions of geophysical data over a synthetic model of the Flin Flon nickel deposit. We simulated several surveys over the area to help delineate the ore deposits.
# The goal is to use airborne geophysics to characterize the physical property and shape of the ore body and host rocks. This case study focuses on the following three datasets and respective physical properties:
#
# - [Direct-current resistivity (DCR)](dc-data) -> resistivity
# - [Magnetic Total Field (TMI)](magnetic-data) -> magnetization
# - [Full-tensor gravity gradiometry (FTG)](ftg-data) -> density
#
# The datasets are first inverted independently ([Figure 1](standalone)), then jointly with a cross-gradient coupling constraint ([Figure 2](joint)).
#
# The following sections provide details about the processing and results. A compilation `geoh5` project can be found [here]()
#
# - [Background information](background.ipynb)
# - [Data](data.ipynb)
# - [Mesh design](mesh_design.ipynb)
# - [Unconstrained inversions](unconstrained_inversion.ipynb)
# - [Joint inversion](joint_inversion.ipynb)
