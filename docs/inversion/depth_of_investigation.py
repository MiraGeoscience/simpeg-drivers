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

# # Depth of Investigation
#
# In geophysics, "depth of investigation" refers to the maximum depth below the surface from which a geophysical survey can reliably measure. It depends on factors like the survey design and physical properties of the subsurface material. Several strategies have been proposed to assess uncertainties in models recovered from inversion. Nabighian & Macnae (1989) used a skin depth approach for electromagnetic surveys, assuming a background halfspace resistivity. Li&O (1999) implemented a cut-off value based on two inverted models obtained with slightly different assumptions. Christiansen & Auken (2012) proposed a mask based on the sum-square of sensitivities to estimate a volume of low confidence. In the following, we discuss the algorithm and implementation of the sensitivity cutoff strategy.

# ## Sensitivities
#
# The sensitivity matrix is calculated as part of the optimization problem solved by SimPEG while inverting geophysical data.  The sensitivity matrix represents the degree to which each predicted datum changes with respect to a perturbation in each model cell.  It is given in matrix form by
#
# $$
# \mathbf{J} = \frac{\mathbf\partial{F}(\mathbf{m})}{\partial{\mathbf{m}}}
# $$
#
# where $\mathbf{m}$ is the model vector, and $F(\mathbf{m})$ represents the forward modelling operation as a function of the model.  The sensitivity matrix $\mathbf{J}$ is a dense array with dimensions $N\times M$, where $N$ is the number of data and $M$ are the number of mesh cells.
#
# The depth of investigation mask is a property of the cells of the mesh only so the rows of the sensitivity matrix (data) are sum-square normalized as follows.
#
# $$
# \mathbf{J}_{norm} = \left[\sum_{n=1}^{N}\left(\frac{\mathbf{J}_{n:}}{w_n}\right)^{2}\right]^{(1/2)}
# $$
#
# where $w_n$ are the data uncertainties associated with the $n^{th}$ datum.
#
# The resulting vector $J_{norm}$ can then be thought of as the degree to which the aggregate data changes due to a small perturbation in each model cell.  The depth of investigation mask is then computed by thresholding those sensitivities

# ## Thresholding
#
# The depth of investigation can be estimated by assigning a threshold on the sum-squared sensitivity vector.  This can be done as a percentile, percentage, or log-percentage.  In the percentile method, the mask is formed by eliminating all cells in which the sensitivity falls below the lowest $n$% of the number of data where $n$ is the chosen cutoff.  In the percent method the data are transformed into a percentage of the largest value
#
# $$
# d_{scaled} = \frac{100 \cdot d}{max(d)}
# $$
#
# and the mask is formed by eliminating all cells in which the sensitivity falls below the lowest $n$% of the data values where $n$ is the chosen cutoff.  Finally, the log-percent mask transforms the data into log-space before carrying out the percentage thresholding described above.

# ## Usage
#
# The depth of investigation methods based on sensitivity cutoffs described above are exposed to Geoscience ANALYST Pro Geophysics users through a ui.json interface.  In order to save the sensitivities during a SimPEG inversion, the 'Save sensitivities' option must be selected from the 'Optional parameters' tab of the SimPEG inversion ui.json window.
#
# ![save_sensitivities](./images/save_sensitivities.png)
#
# This will result in a new model generated and saved into the computational mesh at each iteration.
#
# ![sensitivity_models](./images/sensitivity_models.png)
#
# The ui.json interface allows the user to select a mesh from the **simpeg-drivers** result and any of the generated sensitivity models, a cutoff threshold, method, and optional name for the output.
#
# ![interface](./images/uijson.png)
#
# The cutoff methods are selectable in the dropdown
#
# ![cutoff_options](./images/cutoff_options.png)
#
# Whatever the options, the application will create a sensitivity cutoff mask saved on the mesh
#
# ![mask](./images/sensitivity_mask.png)
#
# which can then be applied to any of the iterations to show only the cells that exceeded the sensitivity threshold.
#
# ![apply_mask](./images/apply_mask.png)
#
# ![masked_model](./images/masked_model.png)
