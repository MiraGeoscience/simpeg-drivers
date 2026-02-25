.. _parallelization:

Parallelization
===============

For a given inversion routine, the problem can be decomposed into a series of sub-problems, or tiles, each assigned a mesh and a survey. During the inverse process, predicted data and derivatives are continuously requested from the sub-problems. These operations are parallelized within each sub-problem, as well as externally such that sub-problems can be computed concurrently.


.. figure:: ./images/distributed_parallelization.svg
    :align: center
    :width: 80%

    Schematic representation of the computing elements of a tiled inversion. Each tile is assigned a mesh and a survey, with array operations parallelized by dask bookending a direct solvers. The tiles can be distributed across multiple workers, each with a limited number of threads to optimize performance. Only 1-dimensional arrays are returned to the main process.

This following sections describe the different level of parallelization used by the inversion routines and how to optimize resources.


Direct Solvers
--------------

The direct solvers are used for all methods evaluated by partial differential (PDE) equations, such as electromagnetics and electric methods. The `Pardiso <https://github.com/simpeg/pydiso>`_ and `Mumps <https://gitlab.kwant-project.org/kwant/python-mumps>`_ solvers are parallelized using OpenMP. Note that the current implementation of the solvers are not thread-safe, and can therefore not be shared within parallel processes.

The number of threads used by the solvers can be set by running the command

.. code-block::

    set OMP_NUM_THREADS=X

before launching the python program. Alternatively, setting ``OMP_NUM_THREADS`` as a local environment variable will set it permanently. The default value is the number of threads available on the machine.

Dask
----

Most operations related to generating arrays are handled by the `dask <https://www.dask.org/>`_ library. A mixture of dask.arrays and dask.delayed calls are used to parallelize the computations across multiple threads. If a direct solver is involved, the dask operations are bookending the solver to avoid thread-safety issues. Otherwise, the dask operations are performed in parallel across the available threads.


Dask.distributed
----------------

For large systems, such as High-Performance Computing (HPC) clusters, the ``dask.distributed`` library can be used to distribute the computation from tiles across multiple ``workers``. It has been found that the performance of direct solvers tend to saturate on large numbers of threads. By spawning multiple processes, each with a limited number of threads, the performance can be improved by running multiple tiles in parallel. The number of workers and threads per worker can be set with the following parameters added to the ui.json file:

.. code-block::

    {
        ...
        "n_workers": X,
        "n_threads": Y,
        "performance_report": true
    }
