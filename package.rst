simpeg-drivers: run SimPEG inversions on GEOH5 files
====================================================
Application to run `SimPEG <https://simpeg.xyz/>`_ inversions
on `GEOH5 files <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/stable/content/geoh5_format/>`_.
Users will be able to directly leverage the powerful visualization
capabilities of `Geoscience ANALYST <https://mirageoscience.com/mining-industry-software/geoscience-analyst/>`_.

.. contents:: Table of Contents
   :local:
   :depth: 3

Documentation
^^^^^^^^^^^^^
`Online documentation <https://mirageoscience-simpeg-drivers.readthedocs-hosted.com/>`_


Installation
^^^^^^^^^^^^
**simpeg-drivers** is currently written for Python 3.10 or higher.

Install within a conda environment
----------------------------------

To install **simpeg-drivers**, you need to install **Conda** first.

We recommend to install **Conda** using `miniforge`_.

.. _miniforge: https://github.com/conda-forge/miniforge

You can install (or update) a conda environment with all the requires packages to run **simpeg-drivers**.
To do so you can directly run the **install.bat** file by double left clicking on it.


Install with PyPI
-----------------

You should not install the package from PyPI, as the app requires conda packages to run.
Still, you can install it in a conda environment without its dependencies (``--no-deps``).

To install the **simpeg-drivers** package published on PyPI:

.. code-block:: bash

    pip install -U --no-deps simpeg-drivers


Feedback
^^^^^^^^
Have comments or suggestions? Submit feedback.
All the content can be found on the github_ repository.

.. _github: https://github.com/MiraGeoscience/geoh5py


Visit `Mira Geoscience website <https://mirageoscience.com/>`_ to learn more about our products
and services.


License
^^^^^^^
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Copyright
^^^^^^^^^
Copyright (c) 2024 Mira Geoscience Ltd.
