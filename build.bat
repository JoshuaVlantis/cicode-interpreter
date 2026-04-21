@echo off
REM build.bat — build and install the CiCode VSCode extension on Windows

SET SCRIPT_DIR=%~dp0
SET EXT_DIR=%SCRIPT_DIR%cicode-extension

echo -^> Syncing interpreter into extension bundle...
IF EXIST "%EXT_DIR%\interpreter" RMDIR /S /Q "%EXT_DIR%\interpreter"
XCOPY /E /I /Q "%SCRIPT_DIR%interpreter" "%EXT_DIR%\interpreter"

echo -^> Packaging VSIX...
cd "%EXT_DIR%"
call vsce package --allow-missing-repository --no-dependencies

FOR /F "delims=" %%f IN ('dir /b /o-n "%EXT_DIR%\cicode-*.vsix" 2^>nul') DO (
    SET VSIX=%EXT_DIR%\%%f
    GOTO :found
)
:found
COPY /Y "%VSIX%" "%SCRIPT_DIR%"

echo -^> Installing extension...
call code --install-extension "%VSIX%"

echo.
echo Done! Reload VSCode: Ctrl+Shift+P -^> Developer: Reload Window
pause
