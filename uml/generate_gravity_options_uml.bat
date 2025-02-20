@echo off
setlocal

set project_dir=%~dp0..
set "param_path=%project_dir%\simpeg_drivers\potential_fields\gravity\params.py"
call pyreverse --output puml --all-ancestors --project gravity_params %param_path%

pause

endlocal
