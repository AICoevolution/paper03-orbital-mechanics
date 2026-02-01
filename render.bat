@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM Render Paper 03: Semantic Orbital Mechanics
REM Usage: render.bat [format]
REM   format: pdf (default), html, typst, all

set FORMAT=%1
REM Default to "all" so PDF + HTML + deploy happens in one run
if "%FORMAT%"=="" set FORMAT=all

echo ============================================================
echo  PAPER 03: Semantic Orbital Mechanics
echo  Format: %FORMAT%
echo ============================================================
echo.

cd /d "%~dp0"

REM Clear Quarto cache to ensure fresh figures
echo [1/4] Clearing cache...
if exist ".quarto" rmdir /s /q ".quarto"
if exist "_freeze" rmdir /s /q "_freeze"
if exist "S64-orbital-paper_files" rmdir /s /q "S64-orbital-paper_files"
echo.

REM Handle "all" format - render both PDF and HTML
if /I "%FORMAT%"=="all" (
    echo [2/4] Rendering PDF...
    quarto render S64-orbital-paper.md --to pdf
    if !ERRORLEVEL! NEQ 0 goto :error
    
    echo.
    echo [3/4] Rendering HTML...
    quarto render S64-orbital-paper.md --to html
    if !ERRORLEVEL! NEQ 0 goto :error
    
    goto :deploy_html
)

echo [2/4] Rendering to %FORMAT%...
quarto render S64-orbital-paper.md --to %FORMAT%

if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo [OK] Render complete! Output in _output/

if "%FORMAT%"=="pdf" (
    start "" "_output\S64-orbital-paper.pdf"
    goto :done
)

:deploy_html
REM If rendering HTML (or all), copy outputs into the website public folder
if /I "%FORMAT%"=="html" goto :do_deploy
if /I "%FORMAT%"=="all" goto :do_deploy
goto :done

:do_deploy
echo.
echo [4/4] Deploying to website...

REM Resolve absolute destination path
for %%I in ("%~dp0..\..\..\apps\website\public\_output") do set "DEST=%%~fI"
if not exist "!DEST!" mkdir "!DEST!"

REM Copy main HTML file
copy /Y "_output\S64-orbital-paper.html" "!DEST!\S64-orbital-paper.html" >nul
echo   - Copied S64-orbital-paper.html

REM Copy Quarto assets
if exist "_output\S64-orbital-paper_files" (
    if exist "!DEST!\S64-orbital-paper_files" rmdir /s /q "!DEST!\S64-orbital-paper_files"
    xcopy "_output\S64-orbital-paper_files" "!DEST!\S64-orbital-paper_files" /e /i /q >nul
    echo   - Copied S64-orbital-paper_files/
)

REM Copy figures with P03_ prefix (Paper 03 namespace)
if exist "_output\figures" (
    if not exist "!DEST!\figures" mkdir "!DEST!\figures"
    xcopy "_output\figures\P03_*.*" "!DEST!\figures\" /y /q >nul
    echo   - Copied figures/P03_*
)

echo.
echo [OK] Deployed to: !DEST!
echo     Website path: /_output/S64-orbital-paper.html
goto :done

:error
echo.
echo [ERROR] Render failed. Check errors above.
goto :end

:done
echo.
echo ============================================================
echo  COMPLETE
echo ============================================================

:end
pause

