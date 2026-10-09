@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars32.bat" >nul
dumpbin /disasm "F:\Remaster Framework\source\MDK\MDK95.EXE" | powershell -NoProfile -Command "$input | Select-String -Pattern '54C678' -Context 10,10"
