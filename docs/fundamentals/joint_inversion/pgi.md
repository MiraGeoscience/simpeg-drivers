# Petrophysically Guided Inversion (PGI)

The Petrophysically Guided Inversion (PGI) strategy allows to find commonality between multiple physical property models using a rock classification and petrophysical information. This method is particularly useful when inverting for different physical properties known to share a common petrophysical relationship.

```{figure} images/joint_pgi.svg
------
scale: 200%
align: center
------
Recovered models from (left to right) a gravity and magnetic; (top) without constraints and (bottom) with a petro-physical constraint to encourage clustering of physical properties.
```

For example, petrophysical measurements on rock samples may indicate that geological units in the subsurface are characterized by a specific range of density and magnetization values. By incorporating this information into the geophysical inversion process, we can encourage the recovered physical property models to cluster around these petrophysically plausible values, which can significantly reduce inversion ambiguity and provide a more accurate and robust model of the subsurface.

## Background

The `Petrophysically Guided Inversion` algorithm follows the implementation of {cite:p}`astic_2019`. Within the SimPEG framework, the method is implemented as a regularization term that can be added to any joint inversion problem. The regularization function is defined as

$$\phi_{petro}(\mathbf(m)) = \| \mathbf{W}(\Theta, \mathbf{z}^*) (\mathbf{m} - \mathbf{m}_{ref}(\Theta, \mathbf{z}^*)) \|^2_2$$

where :math:`\mathbf{m}` is the model vector containing all physical properties, :math:`\mathbf{m}_{petro}` is a vector of petrophysically plausible values for each physical property, and :math:`\mathbf{W}_{petro}` is a weighting matrix that controls the strength and covariance of the petrophysical constraint. The regularization term encourages the inversion to find models that are close to the petrophysically plausible values, which can help to reduce inversion ambiguity and improve the accuracy of the recovered models.
