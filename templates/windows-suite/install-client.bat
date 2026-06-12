@echo off
setlocal
cd /d "%~dp0"
if not exist installed mkdir installed
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force 'packages\$client_package_file' 'installed\rim-tir-client'"
echo Installed to %CD%\installed\rim-tir-client
