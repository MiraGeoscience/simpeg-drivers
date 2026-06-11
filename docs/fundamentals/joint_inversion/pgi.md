# Petrophysically Guided Inversion (PGI)

The Petrophysically Guided Inversion (PGI) strategy allows to find commonality between multiple physical property models using a rock classification and petrophysical information. This method is particularly useful when inverting for different physical properties known to share common petrophysical relationships.

```{figure} images/joint_pgi.svg
------
scale: 50%
align: center
------
Recovered models from (left to right) a gravity and magnetic; (top) without constraints and (bottom) with a petro-physical constraint to encourage clustering of physical properties.
```

For example, lab measurements on rock samples may indicate that geological units can be distinguished by their density and magnetic susceptibility distributions. By incorporating this information into the geophysical inversion process, we can encourage the recovered physical property models to cluster around these petrophysically plausible values. This constraint can significantly reduce inversion ambiguity and provide a more accurate and robust model of the subsurface.

## Background

The `Petrophysically Guided Inversion` algorithm follows the implementation of {cite:p}`astic_2019`, within the SimPEG framework. The method is implemented as a regularization term that can be added to the conventional [model objective function](regularization). The regularization function is defined as

$$\phi_{petro}(\mathbf(m)) = \| \mathbf{W}(\Theta, \mathbf{z}^*) (\mathbf{m} - \mathbf{m}_{ref}(\Theta, \mathbf{z}^*)) \|^2_2$$

where $\mathbf{m}$ is the model vector containing all physical properties, $\mathbf{m}_{ref}$ is a vector of petrophysically plausible values for each physical property and membership $\mathbf{z}^*$. The variable $\Theta$ holds the GMM global variables $\{\pi_j ,\mu_j, \sigma_j\}$, which are the weights, means and standard deviations of each $j^{th}$ petrophysical class. The weighting matrix $\mathbf{W}_{petro}$ is updated iteratively to reflect the local constraint of the GMM.

At each iteration of the inversion, the algorithm identifies the most probably unit for each cell (membership). The reference model $\mathbf{m}$ is updated by taking  and weights $\mathbf{W}_{petro}$ GMM is updated using the current model values to find the optimal clustering of physical properties, as well as the membership of each cell (each geological unit it belongs to). The petrophysical regularization term is then updated using the new GMM parameters and model values, and the inversion proceeds to find a new model that minimizes the data misfit and regularization terms.

.. note:: At current time, only the mean $\mu$ of each petrophysical class is updated at each iteration, while the weights, standard deviations and membership are fixed. Future work will include updating all GMM parameters at each iteration.
