@echo off
setlocal EnableDelayedExpansion

call "%~dp0get_conda_exec.bat"
if !errorlevel! neq 0 (
  exit /B !errorlevel!
)

set MY_CONDA=!MY_CONDA_EXE:"=!
call "!MY_CONDA!" activate .conda-env/ && jupyter-book build docs/
start "" "docs/_build/html/index.html"
cmd /k
