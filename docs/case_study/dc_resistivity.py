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
# # Direct-current Resistivity Inversion
#
# This section focuses on the inversion of direct-current (DC) resistivity data using a conventional dipole-dipole array.
#
# <p style="page-break-after:always;"></p>

# (dc-data)=
#
# ## Data
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

# ## Unconstrained Inversion
#
# The direct-current data are inverted with uncertainties assigned based on a background resistivity value, then converted to potentials.
#
# [Add details]
#
# The following figure shows the data fit and models recovered after convergence.
#
# ```{figure} ./images/dc_model_TOP.png
# ---
# height: 400px
# name: dc_model_TOP.png
# ---
# (Top) (left) Observed and (right) predicted apparent resistivity data after convergence.
#
# (Bottom)
# (Left) Horizontal section at 240 m elevation through the compact density model.
# (Right) Vertical NS section through the recovered smooth resistivity model.
# ```
#
# We note a large contrast in conductivity in plan view, mostly limited as near-surface layer. This feature can be explained by the conductive tailings.
#
# <p style="page-break-after:always;"></p>
