@echo off
chcp 65001 >nul
title Sanal Kamera Stüdyosu

cd /d "%~dp0"

set PYTHON_EXE=C:\Users\aslan\AppData\Local\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    where py >nul 2>&1 && (
        set PYTHON_EXE=py -3.12
    ) || (
        set PYTHON_EXE=python
    )
)

echo Sanal Kamera Stüdyosu Başlatılıyor...
start "" "%PYTHON_EXE%" "main.py"
