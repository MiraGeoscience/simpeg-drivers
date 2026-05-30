# Fundamentals

This module documents the use of [SimPEG](https://simpeg.xyz/) for
geophysical data inversion with user-interface (UIjson) made available
through the [Mira
Geoscience-geoapps](https://mirageoscience-geoapps.readthedocs-hosted.com/)
project. While the code itself has its own documentation, there is a
need to demonstrate the effect of parameters controlling the inversion.
This document is meant to be a reference guide with practical examples
to help practitioners with their inversion work.

- [Background](background): An overview of the inversion framework.
- [Data Fit](data_misfit): Assigning uncertainties and global target
  (data misfit).
- [Regularization (Constraints)](regularization): Adding modeling
  constraints (regularization).
- [Mesh Design](mesh_design): Designing an inversion mesh.
- [Joint/Coupling Strategies](joint_inversion): Inverting multiple
  geophysical surveys.
- [Depth of Investigation](depth_of_investigation): Using sensitivities
  to set depth extents

![inversion_ui](./images/inversion_ui.png)
