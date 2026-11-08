@echo off
rem Inicializacao com terminal para diagnostico. Para jogar, abra iniciar.pyw.
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python main.py
) else (
    py -3 main.py
)
if errorlevel 1 pause
