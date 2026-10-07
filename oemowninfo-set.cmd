@echo off
where py >nul 2>nul
if errorlevel 1 goto python
py -3 "%~dp0oemowninfo_set.py" %*
exit /b %errorlevel%
:python
python "%~dp0oemowninfo_set.py" %*
exit /b %errorlevel%
