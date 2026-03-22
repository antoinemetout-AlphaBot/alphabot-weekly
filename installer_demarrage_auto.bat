@echo off
title AlphaBot - Installation Demarrage Automatique

echo.
echo ================================================
echo   ALPHABOT - DEMARRAGE AUTOMATIQUE
echo   Lundi-Vendredi, 7h30
echo ================================================
echo.

set ALPHABOT_DIR=C:\Users\antoi\OneDrive\Desktop\Alphabot
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo Dossier AlphaBot : %ALPHABOT_DIR%
echo.

REM Creer le script qui sera lance au demarrage de Windows
echo @echo off > "%STARTUP%\AlphaBot_Orchestrateur.bat"
echo title AlphaBot Weekly - Orchestrateur >> "%STARTUP%\AlphaBot_Orchestrateur.bat"
echo cd /d "%ALPHABOT_DIR%" >> "%STARTUP%\AlphaBot_Orchestrateur.bat"
echo python orchestrateur.py >> "%STARTUP%\AlphaBot_Orchestrateur.bat"
echo pause >> "%STARTUP%\AlphaBot_Orchestrateur.bat"

if exist "%STARTUP%\AlphaBot_Orchestrateur.bat" (
    echo OK ! Installation reussie.
    echo.
    echo L'orchestrateur se lancera automatiquement
    echo a chaque connexion Windows.
    echo.
    echo Fichier cree dans :
    echo %STARTUP%\AlphaBot_Orchestrateur.bat
    echo.
    echo IMPORTANT : lance le PC avant 8h30 pour ne pas
    echo rater les tweets du matin.
) else (
    echo ERREUR - Essaie en clic droit - Executer en tant qu'administrateur
)

echo.
pause
