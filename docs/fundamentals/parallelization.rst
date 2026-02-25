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

A direct solvers is used for any method evaluated by partial differential (PDE) equations, such as electromagnetics and electric surveys. The `Pardiso <https://github.com/simpeg/pydiso>`_ and `Mumps <https://gitlab.kwant-project.org/kwant/python-mumps>`_ solvers are parallelized using  during the factorization and backward substitution calls. Note that the current implementation of the solvers are not thread-safe, and can therefore not be shared across parallel processes. Any level other parallelization needs to occur outside the direct solver calls, or encapsulated within a distributed process.

The number of threads used by the solvers can be set by running the command

.. code-block::

    set OMP_NUM_THREADS=X

before launching the python program. Alternatively, setting ``OMP_NUM_THREADS`` as a local environment variable will set it permanently. The default value is the number of threads available on the machine.

Dask
----

Most operations related to generating arrays are handled by the `dask <https://www.dask.org/>`_ library. A mixture of dask.arrays and dask.delayed calls are used to parallelize the computations across multiple threads. The dask operations are performed in parallel across the available threads. Sensitivity matrices can optionally be stored on disk using the `zarr <https://zarr.readthedocs.io/en/stable/>`_ library, which is optimized for parallel read/write access. If a direct solver is involved, the dask operations are bookending the solver to avoid thread-safety issues. Dask.arrays are converted to numpy arrays before being passed to the direct solvers, and before being returned to the main process. Only 1-dimensional arrays are returned to the main process, while higher-dimensional arrays are kept as dask.arrays within the sub-problems.


Dask.distributed
----------------

It has been found that the performance of direct solvers tend to saturate on large numbers of threads. This can be alleviated by spawning multiple processes, each with a limited number of threads, running concurrently. For large systems with sufficient memory available, such as High-Performance Computing (HPC) clusters, the ``dask.distributed`` library can be used to split the computation from tiles across multiple ``workers``.
The number of ``workers`` and ``threads`` (per worker) can be set with the following parameters added to the ui.json file:

.. code-block::

    {
        ...
        "n_workers": X,
        "n_threads": Y,
        "performance_report": true
    }

Where ``n_workers`` is the number of processes to spawn, and ``n_threads`` is the number of threads to use for each process. Setting ``performance_report`` to true will generate an ``html`` performance report at the end of the inversion, which can be used to identify bottlenecks and optimize the parallelization settings.

It is good practice to set an even number of threads per worker to optimize the load. Setting too many workers with too few threads can lead to increased overhead from inter-process communication, while setting too few workers with too many threads can lead to saturation of the direct solvers and reduced performance. For example, if the machine has 32 threads available, setting 4 workers with 8 threads each will fully use the resources.

It is also recommended to set the number of workers as a multiple of the number of tiles, to ensure that all workers are utilized. For example, if there are 8 tiles, setting 4 workers will allow each worker to process 2 tiles concurrently. If fewer tiles than workers are available, the program will automatically split surveys into smaller chunks, while preserving the same mesh, to ensure even load across the workers. This is less efficient than having a dedicated optimized mesh per tile, but will still provide performance benefits.
