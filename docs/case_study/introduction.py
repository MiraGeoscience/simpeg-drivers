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
# This chapter summarizes the work completed by Mira Geoscience to validate the algorithms and inversion codes developed during the Accelerated Development project for Vale S.A.
#
# After consulting with Vale's exploration team, the decision was made to focus on a southern portion of Carajas-Block 3 site. Several surveys have been flown over the area to help delineate known ore deposits and to identify potential extension zones.
# The goal is to use airborne geophysics to characterize the physical property and shape of the ore body and host rocks. This case study focuses on the following three datasets and respective physical properties:
#
# - [Time-domain EM (HeliTEM)](atem-data) -> resistivity
# - [Magnetic Total Field (TMI)](magnetic-data) -> magnetization
# - [Full-tensor gravity gradiometry (FTG)](ftg-data) -> density
#
# The datasets were first inverted independently ([Figure 1](standalone)), then jointly with a cross-gradient coupling constraint ([Figure 2](joint)).
#
# The following sections provide details about the processing and results. A compilation `geoh5` project can be found [here](https://mirageoscience-my.sharepoint.com/:u:/p/dominiquef/ETI3rho9sdVIqvYoAclE-xMBxrrieDzf0oF6gJIyCzlkxQ?e=yaJ6ry)
#
# - [Background information](background.ipynb)
# - [Data](data.ipynb)
# - [Mesh design](mesh_design.ipynb)
# - [Unconstrained inversions](unconstrained_inversion.ipynb)
# - [Joint inversion](joint_inversion.ipynb)
