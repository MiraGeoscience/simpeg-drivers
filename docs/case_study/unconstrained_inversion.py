# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                     '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

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
# # Unconstrained inversions
#
# In preparation for the joint inversion, we first inverted each dataset independently. It serves as a quality control step for data uncertainties estimation and mesh design. We can solve possible convergence issues before attempting to couple the physical property models in a joint process.
#

# ## Magnetic inversion
#
# The airborne magnetic data were inverted over a range of uncertainties in order to achieve an adequate data fit. Following the smooth solution, a series of IRLS iterations were performed to recover an alternate, more compact model. The following figure shows sections through the recovered models and compares the observed and predicted data.
#
#
# ```{figure} ./images/mag_model_TOP.png
# ---
# height: 400px
# name: mag_model_TOP
# ---
# (Top) (left) Observed and (right) predicted data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models.
# ```
#
#
# [Add more here]
#
#
# <p style="page-break-after:always;"></p>

# ## Ground gravity inversion
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

# ## Gravity gradiometry inversion
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

# ## Direct-current inversion
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
