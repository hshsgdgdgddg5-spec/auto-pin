@echo off
title Pinterest Otomasyonunu Durdur
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq Pinterest*" 2>nul
echo Pinterest Otomasyonu durduruldu.
pause
