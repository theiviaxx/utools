@echo off

setlocal

if not exist %USERPROFILE%\Documents\maya\ubd (mkdir %USERPROFILE%\Documents\maya\ubd)
echo Copying scripts
xcopy .\utools %USERPROFILE%\Documents\maya\ubd\utools /S /Y /I >nul
echo Copying module
xcopy utools.mod %USERPROFILE%\Documents\maya\modules /Y >nul

endlocal