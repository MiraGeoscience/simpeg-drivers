.. _plate_simulation:

Plate Simulation
================

The plate-simulation application is a tool for simulating geophysical data over
a simple two-layer earth model with plate(s).  It relies on the
`discretize <https://discretize.simpeg.xyz/en/main/>`_
and `SimPEG <https://simpeg.xyz/>`_ projects to create a refined octree mesh and
simulate data over the parameterized model.  The mesh, model and simulation
details are parameterized in a ui.json file that can be rendered in
`Geoscience ANALYST Pro <https://www.mirageoscience.com/mining-industry-software/geoscience-analyst-pro/>`_.

.. figure:: /plate-simulation/images/index.png
   :align: center
   :width: 50%


.. toctree::
   :maxdepth: 1

   standalone
   sweep
   match
