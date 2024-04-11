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
# # Unconstrained inversions
#
# In preparation for the joint inversion, we first inverted each dataset independently. It serves as a quality control step for data uncertainties estimation and mesh design. We can solve possible convergence issues before attempting to couple the physical property models in a joint process.
#

# ## Magnetic vector inversion
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
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact magnetization models. The outline of the inferred ore shell is shown in gray for reference.
# ```
#
# We note a somewhat good correlation between the shape of the inferred ore shell and magnetic model. The magnetization appears to be shifted southward and at depth, as seen in profile.
#
#
# ```{figure} ./images/mag_model_NS.PNG
# ---
# height: 400px
# name: mag_model_NS
# ---
# (Top) Profile comparing the observed and predicted data along a North-South line directly above the central HF unit.
# (Bottom) North-South section through the compact magnetization model directly below the data profile. Outline of the
# hematite shell is shown in pink for reference.
# ```
#
# The strong magnetic response is likely due to a unit directly adjacent and below the jaspelite and hematite body.
#
# Results of this inversion can be found [here](https://mirageoscience-my.sharepoint.com/:u:/p/dominiquef/EQvvdryKs2ZJmmuqtl3mnukB3BX-dr2_FGwAc5gJtVgI7g?e=YYbof7).
#
# <p style="page-break-after:always;"></p>

# ## Gravity gradiometry inversion
#
# The airborne tensor terrain corrected (2.67 g/cc) gravity data were also inverted in the same fashion. A floor uncertainty value of 20 Eotvos was assigned to all the components.
#
#
#
# ```{figure} ./images/grav_model_TOP.png
# ---
# height: 400px
# name: grav_model_TOP
# ---
# (Top) (left) Observed and (right) predicted gzz data after convergence of the L2 (smooth) solution. Most of the data is well recovered.
#
# (Bottom) Horizontal slice at 255 m elevation for (left) the smooth and (right) compact density contrast models. The outline of the inferred ore shell is shown in gray for reference.
# ```
#
# We note a slight correlation to the shape of the inferred hematite body. We see little correlation with the jaspelite unit.
#
#
# ```{figure} ./images/grav_model_NS.png
# ---
# height: 400px
# name: grav_model_NS
# ---
# (Top) Profile comparing the observed and predicted data along line passing roughly over the jaspelite unit.
# (Bottom) North-South section through the compact density model. Outline of the
# hematite shell is shown in pink for reference.
# ```
#
# The strong density response is likely due to a unit directly adjacent and below the jaspelite and hematite body.
#
#
# Results of this inversion can be found [here](https://mirageoscience-my.sharepoint.com/:u:/p/dominiquef/Efv1bjHyiL1HqDnVMpyNyawBs4GxPgSCaYLfpqldbiJL8w?e=kG59gt).
#
# <p style="page-break-after:always;"></p>

# ## Time-domain inversion
#
# Inverting electromagnetic data continues to be challenging, both from a numerical and a practical standpoint. Solving differential equations at scale requires a large amount of computer resources, while practitioners also need to content with many numerical details that can affect the inversion process. Within the scope of this accelerated development project, Mira was mandated to help tackle both issues by implementing the user-interface and computational mechanism for the inversion of frequency and time-domain data.
#
# ```{figure} ./images/tem_ui.png
# ---
# height: 400px
# name: tem_ui
# ---
# User interface created for time-domain inversion. Inversion mechanisms were developed for both airborne and ground (large-loop) systems.
# ```
#
# Several rounds of optimization and parallelization were applied to the SimPEG code base, reducing the runtime by a factor of four, roughly. For this project, computations were performed on Microsoft Azure cloud services.  The current runtime for the selected 750 sources, 15 time channels and 420k cells averages 1:40 hours per iteration (40 hours total) on a Standard HC44rs (44 vcpus, 352 GiB memory) node.
#
# The following figure shows the data fit and models recovered after convergence.
#
# ```{figure} ./images/res_model.png
# ---
# height: 400px
# name: res_model
# ---
# (Left) Horizontal section at 240 m elevation through the compact density model. Outline of the hematite shell is shown in grey for reference.
#
# (Right)
# (Top) Profile comparing the observed and predicted data along-line passing roughly over the jaspelite unit.
# (Bottom) Vertical NS section through the recovered smooth resistivity model.
# ```
#
# We note a large resistivity anomaly on the western portion of the model - likely due to IP. There is a identifiable correlation between the shape of the hematite and jaspelite and a recovered moderately resistive zone.
#
# Results of this inversion can be found [here](https://mirageoscience-my.sharepoint.com/:u:/p/dominiquef/EYSVKfs9aOJCpSKGJUBN6WMBWOTFa0dH7Jg6BRpRxVjnxg?e=a2kQKU).
#
# <p style="page-break-after:always;"></p>
