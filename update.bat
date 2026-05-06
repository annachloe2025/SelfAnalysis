@echo off
REM ============================================================
REM  SelfAnalysis - commit source + deploy site to GitHub Pages
REM  Double-click this file to update the site.
REM ============================================================

REM Use UTF-8 for Japanese commit messages
chcp 65001 > nul

cd /d C:\Users\hoeho\Documents\Claude\MyProfile\SelfAnalysis

echo.
echo ================================================================
echo   SelfAnalysis  -  update and publish
echo ================================================================
echo.

REM Ask for a commit message (press Enter for default)
set "MSG="
set /p MSG=Commit message (press Enter for default):
if "%MSG%"=="" set "MSG=Update self analysis"

echo.
echo [1/4] Staging changes ...
git add .

echo.
echo [2/4] Committing ...
git commit -m "%MSG%"
if errorlevel 1 echo   (nothing to commit, or commit skipped)

echo.
echo [3/4] Pushing to GitHub ...
git push
if errorlevel 1 (
    echo.
    echo   ERROR: git push failed. Check the messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Deploying site to GitHub Pages ...
python -m mkdocs gh-deploy
if errorlevel 1 (
    echo.
    echo   ERROR: mkdocs gh-deploy failed. Check the messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Done!
echo   Site URL: https://annachloe2025.github.io/SelfAnalysis/
echo ================================================================
echo.
pause
