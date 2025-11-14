@echo off
echo ====================================
echo Building Store Automation EXE
echo ====================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller build.spec --clean

echo.
echo [3/4] Checking build result...
if exist "dist\autify.exe" (
    echo.
    echo [4/4] Copying config.json to dist folder...
    copy config.json dist\config.json
    copy Theme6.zip dist\Theme6.zip
    echo.
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo ====================================
    echo.
    echo Executable created: dist\autify.exe
    echo Config file copied: dist\config.json
    echo Theme file copied: dist\Theme6.zip
    echo.
) else (
    echo.
    echo ====================================
    echo BUILD FAILED!
    echo ====================================
    echo Please check the errors above.
    echo.
)

pause
