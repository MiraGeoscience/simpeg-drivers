
Setup for development
=====================

.. contents:: Table of Contents
   :local:
   :depth: 2

After you have cloned the Git repository, you will need to:

#. create the Conda environment lock files for the dependencies
#. create a virtual Conda environment for development, where to install the
   dependencies of the project
#. execute the tests
#. setup Git LFS if needed
#. configure the pre-commit hooks for static code analysis and auto-formatting
#. configure the Python IDE (PyCharm)


.. _conda-lock: https://conda.github.io/conda-lock/
.. _Poetry: https://python-poetry.org/
.. _pipx: https://pipxproject.github.io/pipx/
.. _pre-commit: https://pre-commit.com/
.. _py-deps-lock: https://github.com/MiraGeoscience/py-deps-lock


Create the Conda lock files and environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install internal tool ``py-deps-lock`` to create the Conda environment lock files,
and the local development environment. ``py-deps-lock`` is a wrapper around `conda-lock`_.

See details in the `py-deps-lock`_ documentation.

To install ``py-deps-lock`` with `pipx`_, run the command::

    $ pipx install git+https://github.com/MiraGeoscience/py-deps-lock


This expose commands to the execution ``PATH``:

- create-dev-env
- deps-lock


Create the Conda environment lock files
---------------------------------------
First, create the Conda environment lock files (``*.conda.lock.yml``) for the dependencies defined
in `pyproject.toml`_. From the root of the project, run the command::

    $ deps-lock

It will create or replace the ``*.conda.lock.yml`` files in the ``environments`` folder:
one for runtime dependencies, and one for development dependencies (with the ``-dev`` suffix),
for each combinations of Python versions and platforms
(platforms are specified in ``conda-lock`` section of the ``pyproject.toml``).

These files will be used by installation script and to create the development environment.


Install the Conda environment
-----------------------------

For development, you need a **Conda** environment. From the root of the project, run the command::

    $ create-dev-env

This command install a local environment at the base of your repository: ``.conda-env``.
This environment should automatically be recognized by the Conda installation.

To activate this environment, run the following command from the root of the project::

    $ conda activate ./.conda-env


Updating dependencies
^^^^^^^^^^^^^^^^^^^^^

Dependencies are listed in `pyproject.toml`_ with version constraints.
Versions are then locked using ``deps-lock`` as previously described.

Anytime dependencies are added to or removed from the ``pyproject.toml`` file,
regenerate the Conda environment lock files, re-running ``deps-lock`` from command line.

Regenerate the Conda environment lock files as well when you want to fetch newly
available versions of the dependencies (typically patches, still in accordance with
the specifications expressed in ``pyproject.toml``).


Adding a dependency
-------------------
First install the dependency using ``conda``:

    $ conda install -p ./.conda-env my_new_dep

Then update the list of dependencies in `pyproject.toml`_ with a suited version constraint
(if for development only, place it under section ``[tool.poetry.group.dev.dependencies]``).

For example, if ``conda`` installed version 1.5.2 of ``my_new_dep``,
then add ``my_new_dep="^1.5.2"``.

Do not forget to regenerate the Conda environment lock files.


How to use **Poetry** to update the dependency list (optional)
--------------------------------------------------------------
`Poetry`_ provides a command line interface to easily add or remove dependencies:

    (path/to/.conda-env) $ poetry add another_package --lock

Note the ``--lock`` option, that simple creates or updates the lock file, without Poetry installing anything.
``poetry`` would install the package through ``pip`` while we want dependencies to be installed through ``conda``
so that they match the version pinned by ``conda-lock``.

One limitation though: Poetry will look for packages in PiPY only and not in the Conda channels.
The version selected by Poetry might thus not be available for Conda.

To install ``Poetry`` on your computer, refer to the `Poetry`_ documentation.


Configure the pre-commit hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`pre-commit`_ is used to automatically run static code analysis upon commit.
The list of tools to execute upon commit is configured in the file `.pre-commit-config.yaml`_.

pre-commit can be installed using a Python installation on the system, or one from a Conda environment,
or through `pipx`_.

- To install ``pre-commit`` using ``pipx`` (recommended)::

    $ pipx install pre-commit

- To install ``pre-commit`` using Python (and pip) in your system path::

    $ pip install --user pre-commit

- Or to install from an activated Conda environment::

    $ conda install -c conda-forge pre-commit

Then, in either way, install the pre-commit hooks as follow (**current directory is the project folder**)::

    $ pre-commit install

To prepare and check the commit messages, you can also use the following commands::

    $ pre-commit install -t prepare-commit-msg -t commit-msg

It configures ``pre-commit`` to prepares and checks the commit ensuring it has a JIRA issue ID:
if no ID was provided, it extracts it from the branch name;
if one was provided, it checks it is the same one as in the branch name.

To run pre-commit manually, use the following command::

    $ pre-commit run --all-files

To run only on changes staged for commit::

    $ pre-commit run

If a tool fails running, it might be caused by an obsolete versions of the tools that pre-commit is
trying to execute. Try the following command to update them::

    $ pre-commit autoupdate

Upon every commit, all the pre-commit checks run automatically for you, and reformat files when required. Enjoy...

If you prefer to run pre-commit upon push, and not upon every commit, use the following commands::

    $ pre-commit uninstall -t pre-commit
    $ pre-commit install -t pre-push


Running the tests
^^^^^^^^^^^^^^^^^

Test files are placed under the ``tests`` folder. Inside this folder and sub-folders,
Python test files are to be named with ``_test.py`` as a suffix.
The test function within this files must have a ``test_`` prefix.


Install pytest
--------------
.. _pytest: https://docs.pytest.org/

If you installed  your environment through ``setup-dev.bat``, pytest is already installed.
You can run it from the Conda command (**in your project folder**)::

    $ pytest tests


Code coverage with Pytest
-------------------------
.. _pytest-cov: https://pypi.org/project/pytest-cov/

If you installed  your environment through ``setup-dev.bat``, `pytest-cov`_ is already installed.
It allows you to visualize the code coverage of your tests.
You can run the tests from the console with coverage::

    $ pytest --cov-report html tests

The html report is generated in the folder ``htmlcov`` at the root of the project.
You can then explore the report by opening ``index.html`` in a browser.


Git LFS
^^^^^^^
In the case your package requires large files, `git-lfs`_ can be used to store those files.
Copy it from the `git-lfs`_ website, and install it.

Then, in the project folder, run the following command to install git-lfs::

    $ git lfs install


It will update the file ``.gitattributes`` with the list of files to track.

Then, add the files and the ``.gitattributes`` to the git repository, and commit.

.. _git-lfs: https://git-lfs.com/

Then, add the files to track with git-lfs::

    $ git lfs track "*.desire_extension"


IDE : PyCharm
^^^^^^^^^^^^^
`PyCharm`_, by JetBrains, is a very good IDE for developing with Python.


Configure the Python interpreter in PyCharm
--------------------------------------------

First, excluded the ``.conda-env`` folder from PyCharm.
Do so, in PyCharm, right-click on the ``.conda-env`` folder, and ``Mark Directory as > Excluded``.

Then, you can add the Conda environment as a Python interpreter in PyCharm.

    ..  image:: devtools/images/pycharm-exclude_conda_env.png
        :alt: PyCharm: Exclude Conda environment
        :align: center
        :width: 40%


In PyCharm settings, open ``File > Settings``, go to ``Python Interpreter``,
and add click add interpreter (at the top left):

    ..  image:: devtools/images/pycharm-add_Python_interpreter.png
        :alt: PyCharm: Python interpreter settings
        :align: center
        :width: 80%

Select ``Conda Environment``, ``Use existing environment``,
and select the desired environment from the list (the one in the ``.conda-env`` folder):

    ..  image:: devtools/images/pycharm-set_conda_env_as_interpreter.png
        :alt: PyCharm: Set Conda environment as interpreter
        :align: center
        :width: 80%

Then you can check the list of installed packages in the ``Packages`` table. You should see
this source package and its dependencies. Make sure to turn off the ``Use Conda Package Manager``
option to see also the packages installed through pip:

    ..  image:: devtools/images/pycharm-list_all_conda_packages.png
        :alt: PyCharm: Conda environment packages
        :align: center
        :width: 80%


Run the tests from PyCharm
--------------------------
First, right click on the ``tests`` folder and select ``Mark Directory as > Test Sources Root``:

    ..  image:: devtools/images/pycharm-mark_directory_as_tests.png
        :alt: PyCharm: Add Python interpreter
        :align: center
        :width: 40%

You can now start tests with a right click on the ``tests`` folder and
select ``Run 'pytest in tests'``, or select the folder and just hit ``Ctrl+Shift+F10``.

PyCharm will nicely present the test results and logs:

    ..  image:: devtools/images/pycharm-test_results.png
        :alt: PyCharm: Run tests
        :align: center
        :width: 80%


Execute tests with coverage from PyCharm
----------------------------------------

You can run the tests with a nice report of the code coverage, thanks to the pytest-cov plugin
(already installed in the virtual environment as development dependency as per `pyproject.toml`_).


To set up this option in PyCharm, right click on the ``tests`` folder and ``Modify Run Configuration...``,
then add the following option in the ``Additional Arguments`` field:

    ..  image:: devtools/images/pycharm-menu_modify_test_run_config.png
        :alt: PyCharm tests contextual menu: modify run configuration
        :width: 30%

    ..  image:: devtools/images/pycharm-dialog_edit_test_run_config.png
        :alt: PyCharm dialog: edit tests run configuration
        :width: 60%

select ``pytest in tests``, and add the following option in the ``Additional Arguments`` field::

    --cov-report html

Then, run the tests as usual, and you will get a nice report of the code coverage.


Some useful plugins for PyCharm
--------------------------------
Here is a suggestion for some plugins you can install in PyCharm.

- `Toml`_, to edit and validate ``pyproject.toml`` file.
- `IdeaVim`_, for Vim lovers.
- `GitHub Copilot`_, for AI assisted coding.

.. _PyCharm: https://www.jetbrains.com/pycharm/

.. _Toml: https://plugins.jetbrains.com/plugin/8195-toml/
.. _IdeaVim: https://plugins.jetbrains.com/plugin/164-ideavim/
.. _GitHub Copilot: https://plugins.jetbrains.com/plugin/17718-github-copilot

.. _pyproject.toml: pyproject.toml
.. _.pre-commit-config.yaml: .pre-commit-config.yaml


Copyright
^^^^^^^^^
Copyright (c) 2024 Mira Geoscience Ltd.
