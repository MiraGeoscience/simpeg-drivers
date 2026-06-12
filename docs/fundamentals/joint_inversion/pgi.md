# Petrophysically Guided Inversion (PGI)

The Petrophysically Guided Inversion (PGI) strategy allows to find commonality between multiple physical property models using a rock classification and petrophysical information. This method is particularly useful when inverting for different physical properties known to share common petrophysical relationships.

```{figure} images/joint_pgi.svg
------
scale: 50%
align: center
------
Recovered (left) gravity and (right) magnetic models; (top) without and (bottom) with petro-physical constraints to encourage clustering of physical properties.
```

For example, lab measurements on rock samples may indicate that geological units can be distinguished by their density and magnetic susceptibility distributions. By incorporating this information into the geophysical inversion process, we can encourage the recovered physical property models to cluster around these petrophysically plausible values. This constraint can significantly reduce inversion ambiguity and provide a more accurate and robust model of the subsurface.

## Background

The `Petrophysically Guided Inversion` algorithm follows the implementation of {cite:p}`astic_2019`, within the [simpeg.regularization](https://docs.simpeg.xyz/latest/content/api/generated/simpeg.regularization.PGIsmallness.html) framework. The method relies on a Gaussian Mixture Model (GMM) to classify the subsurface into different geological units, based on the physical property values.

```{figure} images/gaussian_mixture_model.png
------
scale: 50%
align: center
------
Example of a Gaussian Mixture Model (GMM) used to classify the subsurface into three geological units, based on density and susceptibility values. Image borrowed from [SimPEG-Tutorials](https://simpeg.xyz/user-tutorials/plot-inv-1-joint-pf-pgi-full-info-tutorial/)
```

Each geological unit is associated with a petrophysical model that defines the expected distribution of physical properties for that unit, in terms of mean, covariance and proportion (or weight). The GMM is used to assign a membership probability for each cell in the model, which is then used to guide the inversion process towards petrophysically plausible solutions.

The method is implemented as a regularization term that can be added to the conventional [model objective function](regularization). The regularization function is defined as

$$\phi_{petro}(\mathbf{m}) = \| \mathbf{W}(\Theta, \mathbf{z}^*) (\mathbf{m} - \mathbf{m}_{ref}(\Theta, \mathbf{z}^*)) \|_2^2$$

where $\mathbf{m}$ is the model vector containing all physical properties, $\mathbf{m}_{ref}$ is a vector of mean petrophysically values for each physical property in the memberships defined by $\mathbf{z}^*$. The variable $\Theta$ holds the GMM global variables $\{\pi_j ,\mu_j, \sigma_j\}$, defined by a weight, mean and standard deviation of each $j^{th}$ petrophysical classes. The weighting matrix $\mathbf{W}_{petro}$ is updated iteratively to reflect the local constraint of the GMM.

At each iteration of the inversion, the algorithm identifies the most probable unit for each cell (membership). The reference model $\mathbf{m}$ is updated by assigning the mean values from the petrophysical model, using the geological membership of each cell. Likewise, the weighting matrix $\mathbf{W}_{petro}$ is updated using the covariances and weights for the corresponding memberships. From this updated function, the inversion proceeds to find a new model that minimizes the data misfit and regularization terms.

>At current time, only the mean ($\mu_j$) of each petrophysical class is updated at each iteration, while the weights (standard deviations and proportions) and cell membership are fixed at the onset. Future work will include updating all GMM parameters at each iteration.


## Interface

The joint PGI user interface requires the following input parameters:

```{image} ./images/joint_pgi_ui.png
:scale: 50%
:align: center
```

### Joint parameters

- `Group A, B and C`:

  Standalone inversion groups to be included in the joint inversion.
      Up to three groups can be included in the joint inversion, but
      only one is required. Each group should be fully defined and runnable as a
      standalone inversion problem, with its own survey and mesh.

- `Misfit scale A, B and C`:

  For each standalone inversion group, a scaling factor to be
      applied to the misfit function. This allows to scale the
      uncertainties of individual surveys.

### Petrophysical model

- `Inversion mesh`

  The inversion mesh, which must be compatible with the internal forward meshes on the standalone inversions. See details in the [inversion mesh](inversion_mesh) section. The mesh is required to assign the petrophysical model.

- `Model`
  A referenced data identifying the initial membership of each cell. This can be a geological model or a classification of rock units. The reference model of individual inversions is used to assign the mean values of the petrophysical model.

```{image} ./images/petrophysical_model.png
:scale: 25%
:align: center
```

- `Weight`:

  Weight assigned to the PGI regularization term. The higher the value, the more the inversion will try to cluster the physical properties around the petrophysically plausible values. Setting the value to zero will effectively turn off the PGI constraint.


### Advanced parameters

By default, the regularization parameters of the standalone inversions
are used, allowing for maximum flexibility in controlling the character
of individual models. Otherwise, when the `Regularization` group is
activated, global parameters can be used across all the
sub-regularization functions for more consistent behavior.

```{image} images/joint_cross_grad_ui_advanced.png
:scale: 50%
:align: center
```

All other parameters related to the optimization of the standalone
inversions are overridden by the joint inversion framework.

- `Auto-scaling of misfit functions`:

    By default, an auto-scaling of the misfit functions is applied at each iteration, such that the contribution of each survey to the model update is balanced. This is particularly important when the surveys have different units or sensitivities. More details about the auto-scaling strategy can be found in the [](misfit_scaling) section.
