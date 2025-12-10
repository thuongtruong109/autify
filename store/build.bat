@echo off
echo ====================================
echo Building Autify Executable
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
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo ====================================
    echo.
    echo Executable created: dist\autify.exe
    echo Theme file and favicon are embedded in the exe.
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
