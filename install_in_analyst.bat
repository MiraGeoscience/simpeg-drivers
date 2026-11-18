:: Creates a dedicated environment for this package in Geoscience Analyst.
:: Usage: install_in_analyst.bat [-e] [--conda default] [--name <env-name>]
:: Pass -e first for an editable installation; keep this source checkout in place.

@echo off
setlocal EnableDelayedExpansion

set "MIRA_CMD_RUNNER_DIR=%ProgramFiles%\Mira Geoscience\Geoscience ANALYST\CmdRunner"
set "curdir=%~dp0"

pushd "%curdir%"
if not exist ".pixi" mkdir ".pixi"
set "MY_CONDA_ENV_FILE=%curdir%.pixi\analyst-environment.yml"
pixi exec --spec pixi=0.84.2 -- pixi workspace export conda-environment --from-lock-file --platform win-64 --environment runtime "%MY_CONDA_ENV_FILE%"
if errorlevel 1 (
  popd
  pause
  exit /B 1
)

set EXTRA_PIP_INSTALL_OPTIONS=
if "%1" == "-e" (
  set EXTRA_PIP_INSTALL_OPTIONS=-e
  shift
)

"%MIRA_CMD_RUNNER_DIR%\MambaEnvRunner.exe" --install "%MY_CONDA_ENV_FILE%" --with-pip-deps ^
   --run "pip install --no-deps -U --force-reinstall !EXTRA_PIP_INSTALL_OPTIONS! ." %1 %2 %3 %4 %5 %6 %7 %8 %9

set "INSTALL_EXIT_CODE=!errorlevel!"
popd
pause
exit /B %INSTALL_EXIT_CODE%
