@echo off
REM ============================================================
REM  SelfAnalysis - first-time git initialization
REM  Run this ONCE to link the local folder with the GitHub repo.
REM  After this, use update.bat for normal updates.
REM ============================================================

REM Use UTF-8 for Japanese commit messages
chcp 65001 > nul

cd /d C:\Users\hoeho\Documents\Claude\MyProfile\SelfAnalysis

echo.
echo ================================================================
echo   SelfAnalysis  -  initial git setup
echo ================================================================
echo.

REM Check if already initialized
if exist ".git" (
    echo .git folder already exists. Skipping git init.
    echo If you want to re-initialize, delete .git folder first.
    echo.
    pause
    exit /b 0
)

echo [1/7] Initializing git repository ...
git init
if errorlevel 1 (
    echo.
    echo   ERROR: git init failed.
    pause
    exit /b 1
)

echo.
echo [2/7] Renaming default branch to main ...
git branch -M main

echo.
echo [3/7] Adding remote (https://github.com/annachloe2025/SelfAnalysis.git) ...
git remote add origin https://github.com/annachloe2025/SelfAnalysis.git
if errorlevel 1 (
    echo.
    echo   NOTE: remote 'origin' may already exist. Continuing.
)

echo.
echo [4/7] Staging all files ...
git add .

echo.
echo [5/7] Creating initial commit ...
git commit -m "Initial commit: SelfAnalysis project setup"
if errorlevel 1 (
    echo.
    echo   ERROR: initial commit failed. Check git config (user.name / user.email).
    echo.
    echo   Set them with:
    echo     git config --global user.name  "your name"
    echo     git config --global user.email "your@email"
    echo.
    pause
    exit /b 1
)

echo.
echo [6/7] Pushing to GitHub (main branch) ...
git push -u origin main
if errorlevel 1 (
    echo.
    echo   ERROR: git push failed.
    echo.
    echo   If the remote already has commits, you may need to pull first:
    echo     git pull origin main --allow-unrelated-histories
    echo     git push -u origin main
    echo.
    echo   If authentication fails, check your GitHub credentials / Personal Access Token.
    echo.
    pause
    exit /b 1
)

echo.
echo [7/7] First gh-deploy to GitHub Pages ...
python -m mkdocs gh-deploy
if errorlevel 1 (
    echo.
    echo   ERROR: mkdocs gh-deploy failed.
    echo.
    echo   Make sure you have installed dependencies:
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Done!
echo   Repo:     https://github.com/annachloe2025/SelfAnalysis
echo   Site URL: https://annachloe2025.github.io/SelfAnalysis/
echo.
echo   From now on, use update.bat for normal updates.
echo ================================================================
echo.
pause
