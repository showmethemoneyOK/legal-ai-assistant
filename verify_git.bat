@echo off
echo Verifying Git repository...
cd /d "%~dp0"

echo.
echo 1. Git status:
git status

echo.
echo 2. Git log (last commit):
git log --oneline -1

echo.
echo 3. Files in repository:
git ls-files | head -20

echo.
echo 4. Total files committed:
git ls-files | find /c /v ""

echo.
echo Verification complete!
pause