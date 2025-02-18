@echo off
setlocal

REM Set the relative path variable
set "param_path=..\simpeg_drivers\potential_fields\gravity\params.py"

call "pyreverse --output puml --all-ancestors --project gravity_params %param_path%"

pause

endlocal
