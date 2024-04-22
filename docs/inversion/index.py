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

# # Geophysical Inversions
#
# This module documents the use of [SimPEG](simpeg.xyz) for geophysical data inversion within Geoscience ANALYST through the `UIJson <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/latest/content/uijson_format/index.html>`_ rendered user-interface.  This is accomplished by executing driver scripts within the `simpeg-drivers <https://github.com/MiraGeoscience/simpeg-drivers>`_ package. This document is meant to be a reference guide with practical examples demonstrating parameters exposed by the interface and their effect on a given inversion result.
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
