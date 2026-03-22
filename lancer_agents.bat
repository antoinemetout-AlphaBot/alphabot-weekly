@echo off
title AlphaBot - Lancement des Agents
color 0A

echo.
echo  ============================================
echo   ALPHABOT - LANCEMENT AUTOMATIQUE
echo  ============================================
echo.
echo  Demarrage en cours...
echo.

cd /d "C:\Users\antoi\OneDrive\Desktop\Alphabot"

echo  [1/3] Directeur Adjoint en action...
python main.py --adjoint --no-email
echo.

echo  [2/3] Newsletter du jour...
python main.py
echo.

echo  [3/3] Growth Booster...
python main.py --booster --simulation --nb 5
echo.

echo  ============================================
echo   DONE - Tous les agents ont travaille !
echo  ============================================
echo.
pause
