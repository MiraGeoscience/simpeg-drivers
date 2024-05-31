# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                     '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

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

# # Theory
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
