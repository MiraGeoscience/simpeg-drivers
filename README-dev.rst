Setup for development
=====================

Install `Pixi <https://pixi.sh/>`_ 0.84.2 and clone the repository.
Authenticate with Mira Artifactory using your own credentials::

    pixi auth login mirageoscienceltd.jfrog.io

Never add credentials to ``pixi.toml`` or ``pixi.lock``.

Install and test
^^^^^^^^^^^^^^^^

The shared lock covers Windows and Linux with Python 3.12, 3.13 and 3.14::

    pixi install --locked -e py312
    pixi run --frozen -e py312 install
    pixi run --frozen -e py312 test

The ``install`` task installs this checkout in editable mode without changing
locked dependencies, then checks package compatibility. Use ``py313`` to test
Python 3.13, ``py314`` for Python 3.14, or ``pixi run test-pyvers`` to test all versions.
The ``runtime`` environment omits test and lint tools.

On Windows, install the locked runtime into Geoscience Analyst with::

    install_in_analyst.bat
    install_in_analyst.bat -e --name simpeg-drivers-dev

The script exports the locked ``win-64`` runtime, installs its dependencies
through Analyst, and installs this checkout without resolving dependencies
again. Pass ``-e`` first for editable mode; optional ``--conda`` and ``--name``
arguments are forwarded to Analyst. A valid ``pixi.lock`` is required.

To test editable dependencies from sibling checkouts explicitly::

    pixi run -e py312 test-local

This diagnostic task changes the selected environment; reinstall it from the
lock before validating published dependency compatibility.

Updating dependencies
^^^^^^^^^^^^^^^^^^^^^

Keep published package requirements in ``pyproject.toml`` and their Conda/PyPI
environment equivalents in ``pixi.toml`` aligned. Development requirements use
PEP 735 ``dependency-groups``. Update the recipe's matching runtime requirements
when a dependency constraint changes.

Refresh and validate the lock after editing requirements::

    pixi update
    pixi install --locked -e py312
    pixi run --frozen -e py312 install
    pixi run --frozen -e py312 test

Commit ``pixi.lock`` with the manifest changes. Keep branch-resolution examples
commented beside published constraints; public package metadata must not contain
active Git dependencies.

Git hooks
^^^^^^^^^

Install `prek <https://prek.j178.dev/>`_ and use the existing hook configuration::

    prek install
    prek run --all-files
    prek auto-update

The local pylint hook runs in the locked ``py312`` environment.

Git LFS and IDE setup
^^^^^^^^^^^^^^^^^^^^^

Install `Git LFS <https://git-lfs.com/>`_ and run ``git lfs pull`` when tests need
large data files. Configure your IDE to use the interpreter inside
``.pixi/envs/py312`` and exclude ``.pixi`` from source indexing.
Tests live under ``tests`` and use the ``_test.py`` filename suffix.

Copyright
^^^^^^^^^
Copyright (c) 2023-2026 Mira Geoscience Ltd.
