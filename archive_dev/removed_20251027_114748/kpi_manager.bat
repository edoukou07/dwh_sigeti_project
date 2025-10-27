@echo off
echo ========================================
echo    SIGETI KPI Views Management
echo ========================================
echo.

if "%1"=="" goto menu

if "%1"=="deploy" goto deploy
if "%1"=="test" goto test
if "%1"=="summary" goto summary
if "%1"=="help" goto help

:menu
echo Choose an option:
echo 1. Deploy KPI Views
echo 2. Test KPI Views
echo 3. Show KPI Summary
echo 4. Help
echo 5. Exit
echo.
set /p choice=Enter your choice (1-5): 

if %choice%==1 goto deploy
if %choice%==2 goto test
if %choice%==3 goto summary
if %choice%==4 goto help
if %choice%==5 goto exit

:deploy
echo.
echo 🚀 Deploying KPI Views...
echo ========================================
python create_kpi_views.py
echo.
pause
goto menu

:test
echo.
echo 🔍 Testing KPI Views...
echo ========================================
python test_kpi_views.py --test
echo.
pause
goto menu

:summary
echo.
echo 📈 KPI Executive Summary...
echo ========================================
python test_kpi_views.py --summary
echo.
pause
goto menu

:help
echo.
echo SIGETI KPI Views Management Commands:
echo =====================================
echo.
echo deploy    - Deploy all KPI views to database
echo test      - Test all KPI views and show data
echo summary   - Show executive KPI summary
echo help      - Show this help
echo.
echo Usage examples:
echo   kpi_manager.bat deploy
echo   kpi_manager.bat test
echo   kpi_manager.bat summary
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0