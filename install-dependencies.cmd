@echo off
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m pip install --target "%~dp0dependencies" -r "%~dp0requirements.txt"
exit /b %errorlevel%
:python
python -m pip install --target "%~dp0dependencies" -r "%~dp0requirements.txt"
exit /b %errorlevel%
