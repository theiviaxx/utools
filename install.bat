@echo off

setlocal

echo + PLATFORM:win64 utools 0.1 "%~dp0" > %USERPROFILE%\Documents\maya\modules\utools.mod
echo scripts: ./ >> %USERPROFILE%\Documents\maya\modules\utools.mod
echo plug-ins: ./utools/maya/plugins >> %USERPROFILE%\Documents\maya\modules\utools.mod


endlocal