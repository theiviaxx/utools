@echo off

setlocal

::if not exist %USERPROFILE%\Documents\maya\ubd (mkdir %USERPROFILE%\Documents\maya\ubd)
::echo Copying scripts
::xcopy .\utools %USERPROFILE%\Documents\maya\ubd\utools /S /Y /I >nul
::echo Copying module
::xcopy utools.mod %USERPROFILE%\Documents\maya\modules\ /Y >nul
echo + PLATFORM:win64 utools 0.1 "%~dp0" > %USERPROFILE%\Documents\maya\modules\utools.mod
echo scripts: ./ >> %USERPROFILE%\Documents\maya\modules\utools.mod
echo plug-ins: ./utools/maya/plugins >> %USERPROFILE%\Documents\maya\modules\utools.mod


endlocal