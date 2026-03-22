@echo off
chcp 65001 >nul 2>&1
title AlphaBot - Rattrapage Matin
cd /d "%~dp0"

echo Lancement du rattrapage...
echo.

python rattrapage.py

echo.
echo Appuie sur une touche pour fermer.
pause >nul
