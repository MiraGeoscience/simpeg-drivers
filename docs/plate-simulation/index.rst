.. _plate_simulation_index:

Plate Simulation
================

The plate-simulation application is a tool for simulating geophysical data over
a simple two-layer earth model with plate(s).  It relies on the
`discretize <https://discretize.simpeg.xyz/en/main/>`_
and `SimPEG <https://simpeg.xyz/>`_ projects to create a refined octree mesh and
simulate data over the parameterized model.  The mesh, model and simulation
details are parameterized in a ui.json file that can be rendered in
`Geoscience ANALYST Pro <https://www.mirageoscience.com/mining-industry-software/geoscience-analyst-pro/>`_.

.. figure:: /images/plate-simulation/index.png
   :align: center
   :width: 100%

Two other applications are also available to assist users in finding the best plate parameters to match observed data.  The sweep application allows users to run a batch of simulations over a range of plate parameters, while the matching application uses an optimization algorithm to find the best fit between simulated and observed data.

Content:

- :ref:`Basic Usage <plate_simulation_usage>`
- :ref:`Sweep (batch) simulations <plate_simulation_batch>`
- :ref:`Plate Matching <plate_simulation_match>`
