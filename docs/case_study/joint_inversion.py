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

# # Joint Inversion
#
# Following the independent inversions, we proceeded with a joint inversion of all three datasets using a cross-gradient approach. The goal is to constrain the physical property models based on their spatial changes, such that shape and boundaries are consistent with each other. The joint procedure follows the work presented in
# The inversion mechanism and user-interface was developed within the scope of the accelerated development project.
#
# ```{figure} ./images/joint_comparison.png
# ---
# height: 400px
# name: joint_comparison
# ---
# (Top) Inverted models from the three independent inversion of (left) magnetization, (center) density and (right) conductivity.
# (Bottom) Same model sections from joint cross-gradient inversion.
# ```
#
# The following sections focus on each survey and discuss differences between the independent and joint results.
#
# Inversion results in `geoh5` format can be found [here](https://mirageoscience-my.sharepoint.com/:u:/p/dominiquef/ERy_V17E1aRKi-K1fB_9PAwBN7kLie9aoHeyJ7Zzy_xLSg?e=ZnbV3D)

# ## Magnetization model
#
#
# The figure below compares models computed by the (top) joint cross-gradient and (bottom) standalone inversion of the TMI data in both (left) horizontal and (right) vertical North-South oriented cross-section. Both magnetization models have roughly the same amplitude and agree on the general shape of the central anomaly South of the ore shell. We note that the shape of the magnetic anomaly recovered with the joint method appears to be more compact in cross-section. This is likely due to the influence of the density model as already seen in its standalone result.
#
# ```{figure} ./images/joint_mag.png
# ---
# height: 400px
# name: joint_mag
# ---
# (Top) Recovered magnetization models from joint cross-gradient and (bottom) standalone inversion of the TMI data.
# (Left) Horizontal sections and (right) verticel NS sections.
# ```
#
# <p style="page-break-after:always;"></p>

# ## Density model
#
# The figure below compares models computed by (top) joint cross-gradient and (bottom) standalone inversion of gravity tensor data in both (left) horizontal and (right) vertical North-South oriented cross-section. Density values recovered by the joint inversion are significantly more smooth and correlated with the ore shell. In cross-section, we note a much more consistent density layering along topography. The joint model also highlighted a few deeper anomalies previously unseen in the standalone inversion. This is somewhat expected from the independent inversion of tensor data as they are insensitive to bulk property responses, only changes in physical properties.
#
# ```{figure} ./images/joint_density.png
# ---
# height: 400px
# name: joint_density
# ---
# (Top) Recovered density models from joint cross-gradient and (bottom) standalone inversion of the FTG data.
# (Left) Horizontal sections and (right) vertical NS sections.
# ```
#
# <p style="page-break-after:always;"></p>

# ## Resistivity model
#
#
# The figure below compares models computed by the (top) joint cross-gradient and (bottom) standalone inversion of the time-domain (HeliTEM) data in both (left) horizontal and (right) vertical North-South oriented cross-section. Similar to the density model, we note that the distribution of resistivities appears to be more coherent than with the standalone result. A compact moderately high resistivity anomaly appears to coincide with the hematite unit.
#
#
# ```{figure} ./images/joint_resistivity.png
# ---
# height: 400px
# name: joint_resistivity
# ---
# (Top) Recovered resistivity models from joint cross-gradient and (bottom) standalone inversion of the HeliTEM data.
# (Left) Horizontal sections and (right) vertical NS sections.
# ```
#
# <p style="page-break-after:always;"></p>

# ## Interpretation
#
# As a final interpretation step, we proceed with a clustering (kmeans) analysis of the physical property models. The goal is to highlight zones that have common distributions of density, magnetization and resistivity model values. [Figure 25](clustering) compares the 10 clusters obtained with the (left) standalone and (right) joint inversions.
#
# ```{figure} ./images/compare_10clusters.png
# ---
# height: 400px
# name: clustering
# ---
# Kmeans-clustering of physical properties using 10 bins applied to models obtained with (left) standalone and (right) joint inversions.
#
# ```
#
# We note that the physical property model obtained from joint inversion is much simpler to interpret. Variations in clustering are mostly driven by major changes in the density model between the standalone and joint results.
#
# We have attempted to match the color units sharing similar physical property ranges. [Table 2](rec_phys_prop) summarizes the physical property distributions for units closest to the ore bodies and host rocks.
#
# ```{table} Mean physical property values per clusters
# :name: rec_phys_prop
# | Unit | Susceptibility | Density | Resistivity (Ohm.m)|
# | :--- | :--- | :---- | :---- |
# | Jaspelite (Blue) |  0.05    | 2.9      | 1430     |
# | Hematite (Pink) |  0.1   | 3.05      | 1450     |
# | Mafic (Dark green) |  0.03    | 2.67      | 500     |
# ```
#
# Values of density and resistivity fits roughly our previous assumptions of high density and resistivity of the ore bodies. Amplitude of magnetization appears to be higher than expected.

# ## Summary
#
# The joint cross-gradient regularization has a significant impact on the results, generally yielding less complex models with coherent edges. While this result has yet to be validated with ground geological data, the joint models appear to fit fairly well with the inferred ore shell in terms of shape and physical property contrasts. The main benefeciary of the joint approach appears to be the gravity tensor data inversion. This is expected given that gradient data do not carry bulk density information. The FTG data can however provide information about edges and help delineate boundaries between petrophysical units. This is complementary to the bulk response measured by magnetics and EM systems.
