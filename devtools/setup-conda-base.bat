:: Setup the conda base environment with conda-lock
::
:: The script has no parameters, and can be executed by double-clicking
:: the .bat file from Windows Explorer.
::
:: Usage: setup-conda-base.bat

@echo off
setlocal EnableDelayedExpansion

set project_dir=%~dp0..
call %project_dir%\get_conda_exec.bat
if !errorlevel! neq 0 (
  pause
  exit /B !errorlevel!
)

:: install a few packages in the conda base environment
:: - conda-libmamba-solver: for faster dependency solving
:: - conda-lock: for locking the environment
:: - networkx, ruamel.yaml: used by run_conda_lock.py to create the conda environment lock files
call !MY_CONDA_EXE! install -n base conda-libmamba-solver conda-lock networkx ruamel.yaml
call !MY_CONDA_EXE! run -n base conda config --env --set solver libmamba


if !errorlevel! neq 0 (
  echo "** ERROR: Installation failed **"
  pause
  exit /B !errorlevel!
)

pause
cmd /k !MY_CONDA_EXE! activate base
