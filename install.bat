@echo off

setlocal

if not exist %USERPROFILE%\Documents\maya\ubd (mkdir %USERPROFILE%\Documents\maya\ubd)
xcopy .\utools %USERPROFILE%\Documents\maya\ubd\utools /S /Y /I >nul
xcopy utools.mod %USERPROFILE%\Documents\maya\modules /Y >nul

endlocal