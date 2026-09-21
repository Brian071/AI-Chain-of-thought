@echo off
title QwQ-32B CoT Offline AI Suite
echo ========================================================
echo   Starting QwQ-32B CoT Offline AI Suite
echo   Buka browser lokal di http://127.0.0.1:8000
echo ========================================================

if exist "QwQ_Offline_AI.exe" (
    start QwQ_Offline_AI.exe
) else if exist "dist\run\run.exe" (
    start dist\run\run.exe
) else (
    python run.py
)

pause
