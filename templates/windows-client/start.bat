@echo off
setlocal
cd /d "%~dp0"
if not exist data mkdir data
if not exist logs mkdir logs
bin\tir-backend.exe -config config\client.yaml
