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

# # Geophysical Inversions
#
# This module documents the use of [SimPEG](simpeg.xyz) for geophysical data inversion with user-interface (UIjson) made available through the [Mira Geoscience-geoapps](https://geoapps.readthedocs.io/en/latest/) project. While the code itself has its own documentation, there is a need to demonstrate the effect of parameters controlling the inversion. This document is meant to be a reference guide with practical examples to help practitioners with their inversion work.
#
#
# - [Inversion Fundamentals](fundamentals.ipynb): An overview of the inversion framework.
#
# - [Data Misfit](data_misfit.ipynb): Assigning data uncertainties and target.
#
# - [Regularization](regularization.ipynb): Adding modeling constraints on the solution.
#
# - [Joint/Coupling Strategies](joint_inversion.ipynb): Inverting multiple geophysical surveys.
#
# ![inversion_ui](./images/inversion_ui.png)
