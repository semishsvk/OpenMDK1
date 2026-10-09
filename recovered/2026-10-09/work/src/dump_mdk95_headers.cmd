@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars32.bat" >nul
dumpbin /headers "F:\Remaster Framework\source\MDK\MDK95.EXE"
