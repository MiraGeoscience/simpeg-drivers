.. _plate_simulation_batch:

Batch Simulations
=================

The Plate Sweep module provides a user interface for generating and running a batch of simulations by sweeping one or more of the input parameters.  The user can select which parameters to sweep and the range of values for each parameter.  The results of each simulation are stored in a ``*.geoh5`` file named with a unique identifier.



Interface
---------

.. figure:: /plate-simulation/images/sweep/sweep_uijson.png
    :align: center
    :width: 80%

    *Rendered user-interface in Geoscience ANALYST.*

Inputs
^^^^^^

- **Plate simulation**: A Plate Simulation group that contains the input parameters for a single plate simulation, as well as the connection to a SimPEG Forward group. Parameters that are not included in the sweep will be taken from this group and used for all simulations.
- **Output directory**: A directory where the results of each simulation will be stored. Each simulation will be saved in a separate ``*.geoh5`` file named with a unique identifier. The directory is created if it does not exist, otherwise simulations are appended to it.
- **Generate summary file**: A boolean option to generate a summary file in the output directory. The summary file is a ``*.xls`` file that contains the input parameters and results of each simulation, allowing users to easily sort over the range of simulation parameters.
- **Sweep block**: For each the following parameters, users can choose a **starting**, **ending** and **step** value to sweep over a range of values. The application will generate a simulation for each value in the range, while keeping all other parameters constant.
    - **Background**: Over-writing the

Methodology
-----------

Something


Tutorial
--------
To be added.
