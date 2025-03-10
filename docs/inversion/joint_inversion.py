# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Joint Inversion
#
# This section introduces the methodology to invert multiple datasets jointly.

# ## Joint Surveys Inversion
#
#
# As illustrated below, the `joint surveys` program allows to invert multiple datasets at once for a single physical property model. The goal is to combine complementary  information from various geophysical surveys that sense the Earth differently.
#
# ![joint_surveys](./images/joint_surveys.png)
#
# For example, a magnetotelluric survey is mostly sensitive to deep structures but can still be affected by local changes in resistivity near the sensor locations. A ground direct-current survey on the other hand is highly sensitive to near surface changes in resistivity. Inverting both surveys together would provide complementary information that improves our modeling capabilities overall.
#
# This joint inversion problem does not require a coupling term - simply the summation of multiple misfit functions. Extending the objective function described in the [inverse problem](inverse_problem) section, our new misfit function becomes
#
# $$
# \phi_d = \phi_d^A + \phi_d^B + ...
# $$
#
# or
#
# $$
# \phi_d = \sum_{j=A, B, C} \phi_d^j
# $$
#
# Since each misfit tries to update the same model values, the partial derivatives of each function is also a summation, such that
#
# $$
# \frac{\delta \phi_d}{\delta m} = \sum_{j=A, B, C} \frac{\delta \phi_d^j}{\delta m}
# $$
#
# The joint survey inversion user requires a list of standalone inversion groups as input.

# ## Joint Properties Inversion
#
# The more general joint inversion strategy tries to find commonality between different physical properties models.  The goal is to invert for a `common Earth model` based on multiple geophysical surveys that might provide complementary information. For example, one could invert a direct-current resisitivity survey for the thickness of overburden, along with a gravity survey to highlight the density of targets under cover. Both geophysical survey are sensitive to different components of the sub-surface, but can greatly help each other in reducing ambiguity about the position and shape of physical property contrasts.
#
# This kind of joint inversion requires a `coupling` term in order to tie those physical properties together.
#
# ![joint_coupling](./images/joint_coupling.png)
#
#
# In this case, the model $m$ is made up of N-number of sub-models, one per misfit function. The derivatives of the misfit function become
#
# $$
# \frac{\delta \phi_d}{\delta m} = \sum_{j=a, b, c} \frac{\delta \phi_d}{\delta m_j}
# $$
#
# where the subscript $j$ denotes the component of the model (either resistivity, magnetization or density). Each misfit function incluences a different subset of the model.
#
# The following coupling terms are available through the SimPEG framework {cite:p}`heagy_2017`:
#
# - [Cross-gradient](cross-gradient)
# - [Linear Correspondence](linear-correspondence)
#
# - [Petrophysically Guided Inversion (PGI)](pgi)

# (cross-gradient)=
#
# ### Cross-gradient
#
# The `cross-gradient` regularization was first introduced by {cite:p}`gallardo2003` to constrain electrical resistivity and seismic velocity inversions, but the same strategy applies to any physical property models. As the name states, the method employs the cross product on the spatial gradients of models such that
#
# $$
# \phi_c(\mathbf{m_A},\mathbf{m_B}) = \sum_{i=1}^{M} \| \nabla \mathbf{m_A}_i \times \nabla \mathbf{m_B}_i \|^2
# $$
#
# where $\nabla \mathbf{m_A}$ and $\nabla \mathbf{m_B}$ are the gradients for two distinct physical properties (density, magnetization components, resitivity, etc.). Since the cross-product of two vectors is also a vector, we use the total length (l2-norm) of the cross-product. The constraint is small (no impact) if the gradients of the models are either aligned or zero. Conversely, the measure becomes large if edges in the physical models are perpendicular with each other. Since we are attempting to minimize this function, this constraint will force model boundaries to occur at the same location or not at all.
#
# It is possible to constrain more than two physical property models by adding multiple cross-gradient terms for every pair of models such that
#
# $$
# \phi_c(\mathbf{m_A},\mathbf{m_B}, \mathbf{m_C}) = \alpha_{AB} \phi(\mathbf{m_A},\mathbf{m_B}) + \alpha_{AC}\phi(\mathbf{m_A},\mathbf{m_C}) + \alpha_{BC} \phi(\mathbf{m_B},\mathbf{m_C})
# $$
#
# and so on. Each term has a scaling parameter ($\alpha$) to control the importance of specific cross-gradient terms.
#
#
# (linear-correspondence)=
#
# ### Linear Correspondence
#
# To be continued
#
#
# (pgi)=
#
# ### Petrophysically Guided Inversion (PGI)
#
# To be continued

# ## Mesh creation
#
# This section provides details on how to create the forward simulation meshes for each survey in preparation for a joint inversion. While all the misfit functions try to influence a model $m$ defined on a global mesh, individual forward simulations $\mathbb{F}^j(m)$ can be defined on sub-domains adapted to their specific array configurations. For example, an airborne EM simulation may require small cells in the air for numerical accuracy, while a dc-resisitivity survey only requires cells below ground at the transmitter-receiver pole locations.
#
#
# To be continued
#
# <p style="page-break-after:always;"></p>
