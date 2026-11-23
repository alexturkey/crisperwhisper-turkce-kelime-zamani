@echo off
rem EN: double-click, or run in cmd, to install (it asks for a short install folder such as E:\stt). Extra flags go to scripts\kur.ps1, e.g. kur.cmd E:\stt -Kuru (dry run: reports only, changes nothing).
rem TR: cift tikla ya da cmd icinde calistir; kurulum klasorunu sorar (kisa, ornek E:\stt). Ek bayraklar scripts\kur.ps1 dosyasina gider, orn. kur.cmd E:\stt -Kuru (kuru calisma: yalniz rapor, hicbir sey degistirmez).
rem Exit codes / cikis kodlari: those of scripts\kur.ps1 (0 ok, 1 error; with -Kuru: 3 = something missing). Codes and fixes: docs\SIK_HATALAR.md
rem Env: STT_NO_PAUSE=1 (never wait for a key), STT_PAUSE=1 (always wait).
rem No labels and no multi-line blocks on purpose: this file still works if a download converted it to LF line endings.
setlocal
set "STT_DIR=%~dp0"
set "STT_SELF=%~f0"
cd /d "%STT_DIR%"
set "STT_KOK=%~1"
if defined STT_KOK if /i not "%STT_KOK:~0,1%"=="-" shift
if /i "%STT_KOK:~0,1%"=="-" set "STT_KOK="
if not defined STT_KOK set /p "STT_KOK=Install folder, short, no spaces, e.g. E:\stt / Kurulum klasoru (kisa, bosluksuz, orn. E:\stt): "
if not defined STT_KOK echo No folder given / klasor verilmedi.
if not defined STT_KOK set "STT_KOD=2"
if defined STT_KOK call powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%STT_DIR%kur.ps1" -Kok "%STT_KOK%" %1 %2 %3 %4 %5 %6 %7 %8 %9
if defined STT_KOK set "STT_KOD=%ERRORLEVEL%"
echo.
echo Exit code / cikis kodu: %STT_KOD%  (0 = ok / tamam; with -Kuru: 3 = something missing / eksik var). Codes and fixes / kodlar ve cozumler: docs\SIK_HATALAR.md
set "STT_CIFT="
echo %cmdcmdline% | "%SystemRoot%\System32\find.exe" /i "%STT_SELF%" >nul && set "STT_CIFT=1"
if "%STT_PAUSE%"=="1" set "STT_CIFT=1"
if "%STT_NO_PAUSE%"=="1" set "STT_CIFT="
if defined STT_CIFT pause
endlocal & exit /b %STT_KOD%
