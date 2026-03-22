@echo off
title AlphaBot - Orchestrateur 8h-18h
color 0A

echo.
echo  ================================================
echo   ALPHABOT WEEKLY - ORCHESTRATEUR AUTOMATIQUE
echo   Agents actifs de 8h a 18h tous les jours
echo  ================================================
echo.

cd /d "C:\Users\antoi\OneDrive\Desktop\Alphabot"

echo [INFO] Repertoire : %CD%
echo [INFO] Demarrage de l'orchestrateur...
echo.

python orchestrateur.py

pause
