@echo off
title Stop KIRAHT AI Web Server
echo ========================================================
echo   Stopping KIRAHT AI Web HUD (Freeing Port 8000)...
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pids = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique; " ^
  "if ($pids) { " ^
  "    foreach ($pid_val in $pids) { " ^
  "        if ($pid_val -gt 0) { " ^
  "            Write-Host ('Killing PID ' + $pid_val + '...'); " ^
  "            Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue; " ^
  "        } " ^
  "    } " ^
  "    Write-Host 'KIRAHT AI has been stopped successfully.' -ForegroundColor Green; " ^
  "} else { " ^
  "    Write-Host 'No running KIRAHT AI instance found on port 8000.' -ForegroundColor Yellow; " ^
  "}"

timeout /t 3
