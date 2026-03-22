@echo off
title AlphaBot - Live Monitor
color 0B

echo.
echo  ============================================
echo   ALPHABOT LIVE MONITOR
echo  ============================================
echo  Le dashboard va s'ouvrir dans votre navigateur
echo  URL : http://localhost:8080
echo.
echo  Pour arreter : fermez cette fenetre
echo  ============================================
echo.

cd /d "C:\Users\antoi\OneDrive\Desktop\Alphabot"
python monitor.py
