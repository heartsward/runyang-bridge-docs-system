@echo off
REM ==========================================================
REM Runyang Bridge System - Daily Backup
REM Usage: backup_daily.bat [backup_root]
REM   default root: D:\rywd-backup  (C:\rywd-backup if no D drive)
REM   snapshot dir: <root>\YYYYMMDD_HHMMSS\
REM
REM What gets backed up (all four are interdependent):
REM   1. backend\yunwei_docs.db  hot copy via sqlite backup API
REM      (no need to stop backend) + integrity_check
REM   2. backend\uploads\        original files + .json sidecars
REM   3. backend\wiki\           extracted markdown + images + index.db
REM   4. backend\.env            SECRET_KEY etc (SENSITIVE, guard it)
REM   5. backend\task_status\    task state (small)
REM Then prunes old snapshots (keep 14 days, min last 7).
REM
REM Log: <root>\backup.log (self-redirected)
REM Scheduled task example (run once as admin):
REM   schtasks /Create /TN "rywd-daily-backup" /TR "cmd /c C:\rywd\runyang-bridge-docs-system\scripts\backup_daily.bat" /SC DAILY /ST 03:10 /RU SYSTEM /RL HIGHEST /F
REM
REM NOTE: keep this file ASCII-only; cmd reads .bat in the OEM
REM codepage and non-ASCII bytes break parsing (learned the hard way).
REM ==========================================================
setlocal enabledelayedexpansion

REM ---- project root (this script lives in scripts\) ----
set "PROJ=%~dp0.."
for %%I in ("%PROJ%") do set "PROJ=%%~fI"

REM ---- backup root ----
set "BACKUP_ROOT=%~1"
if not defined BACKUP_ROOT (
  if exist "D:\" (set "BACKUP_ROOT=D:\rywd-backup") else (set "BACKUP_ROOT=C:\rywd-backup")
)

REM ---- self-redirect to log (wrap once, guard against recursion) ----
if "%_RYWD_BACKUP_LOGGED%"=="1" goto :main
set "_RYWD_BACKUP_LOGGED=1"
mkdir "%BACKUP_ROOT%" 2>nul
call "%~f0" %* >> "%BACKUP_ROOT%\backup.log" 2>&1
exit /b !errorlevel!

:main
echo.
echo ============================================================
echo [%date% %time%] daily backup start
echo   project: %PROJ%
echo   dest:    %BACKUP_ROOT%

REM ---- snapshot dir name YYYYMMDD_HHMMSS (prune_backups.py format) ----
set "TS="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"`) do set "TS=%%I"
if not defined TS (
  for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul ^| find "LocalDateTime"') do set "DT=%%I"
  set "TS=%DT:~0,8%_%DT:~8,6%"
)
set "DEST=%BACKUP_ROOT%\%TS%"
mkdir "%DEST%" 2>nul

REM ---- python (prefer backend venv; stdlib sqlite3 is all we need) ----
set "PY=%PROJ%\backend\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

REM ---- 1. sqlite hot backup + integrity check ----
"%PY%" "%PROJ%\scripts\backup_db.py" "%PROJ%\backend\yunwei_docs.db" "%DEST%\yunwei_docs.db"
if errorlevel 1 (
  echo [%date% %time%] ERROR: database backup failed, aborting run
  exit /b 1
)

REM ---- 2. uploads ----
robocopy "%PROJ%\backend\uploads" "%DEST%\uploads" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
  echo [%date% %time%] ERROR: uploads copy failed, rc=!errorlevel!
  exit /b 1
)

REM ---- 3. wiki ----
robocopy "%PROJ%\backend\wiki" "%DEST%\wiki" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 (
  echo [%date% %time%] ERROR: wiki copy failed, rc=!errorlevel!
  exit /b 1
)

REM ---- 4. .env (sensitive config) ----
if exist "%PROJ%\backend\.env" (
  copy /Y "%PROJ%\backend\.env" "%DEST%\.env" >nul
  echo   [.env] copied
) else (
  echo [%date% %time%] WARN: backend\.env not found, skipped
)

REM ---- 5. task_status (small, cheap insurance) ----
if exist "%PROJ%\backend\task_status" (
  robocopy "%PROJ%\backend\task_status" "%DEST%\task_status" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP >nul
)

REM ---- 6. retention: keep 14-day window, always at least last 7 ----
"%PY%" "%PROJ%\scripts\prune_backups.py" "%BACKUP_ROOT%" --keep-days 14 --keep-count 7

echo [%date% %time%] daily backup DONE -^> %DEST%
echo ============================================================
exit /b 0
