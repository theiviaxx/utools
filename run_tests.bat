@echo off
setlocal

cd %~dp0

"C:\Program Files\Autodesk\Maya2016\Python\Scripts\py.test.exe" %*

endlocal