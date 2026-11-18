@echo off
setlocal
pushd "%~dp0"

pixi exec --spec pixi=0.84.2 -- pixi install --locked -e py312
if errorlevel 1 goto failed
pixi exec --spec pixi=0.84.2 -- pixi run --frozen -e py312 install
if errorlevel 1 goto failed

popd
pause
exit /B 0

:failed
echo "** ERROR: Installation failed **"
popd
pause
exit /B 1
