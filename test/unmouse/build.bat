@echo off
echo ====================================
echo Building VM Automation EXE
echo ====================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller build.spec --clean

echo.
echo [3/3] Checking build result...
if exist "dist\autify_vm.exe" (
    echo.
    echo [4/4] Copying templates folder to dist...
    xcopy /E /I /Y templates dist\templates
    echo.
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo ====================================
    echo.
    echo Executable created: dist\autify_vm.exe
    echo Templates folder copied: dist\templates\
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
