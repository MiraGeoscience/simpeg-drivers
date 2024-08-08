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

# # Inversion Fundamentals
#
# This section provides the mathematical background to understand the inversion algorithm. We are going to use standard terminology and nomenclature used in the literature as a framework. Even though we are going to use mathematical expressions, it is only a vehicle to help in understanding the influence of different parameters controlling the outcome of an inversion.

# ## Forward simulation
#
# Before we start tackling the inverse problem, it is important to talk about the `forward` simulation. In other words, how does a computer generate geophysical data given a model and topography. We can generally write this in a simple form:
#
# $$
# \mathbf{d} = \mathbf{F}(\mathbf{m})
# $$
#
# where
# - $\mathbf{d}$ is the geophysical data (gravity, magnetic, voltages, etc.)
# - $\mathbf{F}$ is some computer operation handling the physics
# - $\mathbf{m}$ is a discrete model of physical property (density, susceptibility, conductivity, etc.)
#
# Note that the forward simulation $\mathbf{F}(\mathbf{m})$ varies in complexity depending on the type of geophysical survey: from a simple dense arrays for potential fields:
#
# - [Gravity](gravity.ipynb)
# - [Magnetics](magnetic.ipynb)
#
# to elaborate partial differential equations for EM problems:
#
# - [Direct Current](dc_ip.ipynb)
# - [Magnetotellurics](mt.ipynb)
# - [Frequency-Domain EM](frequency_em.ipynb)
# - [Time-Domain EM](time_em.ipynb)
#
# All that matters at this point is that `SimPEG` knows how to compute data given a model $\mathbf{m}$.
#
# ![forward_mag_susc](./images/forward_mag_susc.png)
#
# Figure showing simulated magnetic TMI data over the Flin Flon model (20 m resolution).

# ### Example
#
# Let's look at a simple 2 parameter problem to illustrate this concept:
#
# $$
# 1*x + \:2*y = d \;.
# $$
#
# The same expression can be written as linear operation of matrix $\mathbf{F}$ multiplying a `model` $\mathbf{m}$ such that
#
# $$
# \mathbf{F} \mathbf{m} = \mathbf{d}
# $$
#
# or
#
# $$
# \large[\begin{array}{ccc}
# 1 & 2
# \end{array}\large]\left[\begin{array}{ccc}
# x \\ y
# \end{array}\right] = d\;.
# $$

import numpy as np
from numpy.linalg import LinAlgError


F = np.c_[1, 2]

# For given values for $\mathbf{m}$, we have a way to compute data $\mathbf{d}$. For example, for
# $x = 0.5$ and $y=0.25$

np.dot(F, [0.5, 0.25])

# (inverse_problem)=
#
#
# ## Inverse problem
#
# In a mineral exploration context, we can collect data over the Earth but generally know little about the source of the signal (geology and physical properties). This is where the inversion process is required. In an ideal world we could simply perform the inverse of our forward simulation
#
# $$
# \mathbf{m} = \mathbf{F}^{-1} \mathbf{d}
# $$
#
# but this operation is never possible in practice. First, there are too many unknowns compared to the amount of data, so $\mathbf{F}^{-1}$ does not exist. Secondly, the data are generally noisy so that we would have:
#
# $$
# \mathbf{m} = \mathbf{F}^{-1} (\mathbf{d + e})
# $$
#
# This is referred to as an ill-posed problem. A common way to still find a (good) answer is to formulate inversion as a weighted least-squares optimization problem of the form:
#
# $$
# \underset{\mathbf{m}}{\text{min}}\; \phi(m) = \; \phi_d + \beta \; \phi_m
# $$
#
# such that we have a global function $\phi(m)$ made up of two competing objectives:
#
# - $\phi_d$ is the [data misfit](data_misfit.ipynb) function that measures how well some model ($\mathbf{m}$) can **fit the data**
#
# $$
# \phi_d =\sum_{i=1}^{N}\left(w_i (d_i^{pred} - {d}_i^{obs})\right)^2
# $$
#
# In linear form this can be written as
#
# $$
# \phi_d =(\mathbb{F}(\mathbf{m}) - \mathbf{d}^{obs})^T \mathbf{W}_d^T \mathbf{W}_d (\mathbb{F}(\mathbf{m}) - \mathbf{d}^{obs})\;,
# $$
#
# where the data weights $\mathbf{W}_d$ are diagonal matrices with estimated data uncertainties. More details can be found in the [data misfit](data_misfit.ipynb) module.
#
#
# - $\phi_m$ is a [regularization](regularization.ipynb) function measuring how well we **fit geological assumptions**
#
# $$
# \phi_m =\sum_{i=1}^{N}\left(w_i f(m_i - {m}_i^{ref})\right)^2
# $$
#
# In linear form this can be written as
#
#
# $$
# \phi_m = (\mathbf{m} - \mathbf{m}^{ref})^T \mathbf{R}^T \mathbf{R}(\mathbf{m} - \mathbf{m}^{ref})
# $$
#
# where the operator $\mathbf{R}$ describe all functions used to guide the solution to a reference model $\mathbf{m}_{ref}$. More details can be found in the [regularization](regularization.ipynb) module. A solution for the minimum of the objective function can be computed by taking its partial derivatives with respect to the model and setting it to zero
#
# $$
# \frac{\delta \phi(m)}{\delta m} = \frac{\delta \phi_d}{\delta m} + \beta \frac{\delta \phi_m}{\delta m} = 0
# $$
#
# The two functions are competing for what the model $\mathbf{m}$ should look like - either fit the data ($\phi_d$) at all cost, or stay close to some geological assumptions ($\phi_m$). Finally we have our trade-off parameter $\beta$, that determines the relative importance between these two competing objectives. More details about how the optimal $\beta$ is determined can be found in the [optimization](optimization.ipynb) section.
#
#

# ### Example
#
# We can reuse the two-parameter problem above to illustrate the inverse problem. We are going to ignore the issue of noise for now and simply look at the under-determined problem
# $$
# \large[\begin{array}{ccc}
# 1 & 2
# \end{array}\large]\left[\begin{array}{ccc}
# x \\ y
# \end{array}\right] = 1\;.
# $$
#
# where we are giving data ($d=1$) and a linear operator $\mathbf{F}=[1 \; 2]$.


# Since $\mathbf{F}$ does not have an inverse, we can instead solve the least-norm problem
#
# $$
# \|\mathbf{F} \mathbf{m} -1 \|^2_2
# $$
#
# which can be written as
#
# $$
# \phi_d =(\mathbf{F} \mathbf{m} - 1)^T (\mathbf{F} \mathbf{m} - 1)\;.
# $$
#
# Taking the derivative of $\phi_d$ with respect to the model $\mathbf{m}$ and setting it to zero yields
#
# $$
# \mathbf{m} =(\mathbf{F}^T \mathbf{F})^{-1}(\mathbf{F}^T 1)\;.
# $$
#
# but even here $(\mathbf{F}^T \mathbf{F})^{-1}$ is singular and cannot be inverted directly as shown below

try:
    np.linalg.solve(np.dot(F.T, F), F.T * np.r_[1])
except LinAlgError as error:
    print(error)

# We can get around this by adding a small value to `regularize` the system such that
#
# $$
# \mathbf{m} =(\mathbf{F}^T \mathbf{F} + \delta \mathbf{I})^{-1}(\mathbf{F}^T 1)\;.
# $$

np.linalg.solve(np.dot(F.T, F) + 1e-12 * np.eye(2), F.T * np.r_[1])

# We have found a solution to this under-determined problem: $m = [0.2,\; 0.4]$. This result is known as the `least-norm` solution, which differs from the true answer $m = [0.5, \;0.25]$. Other "better" solutions could be found if more information is provided to the inverse problem to push the model towards expected values. This will be the topic of the [Regularization Section](regularization.ipynb)

# <p style="page-break-after:always;"></p>
