@echo off
chcp 65001 >nul
title ตรวจสอบ Google Sheets
color 0E

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   🔍 ตรวจสอบ Google Sheets                       ║
echo ╚════════════════════════════════════════════════════╝
echo.

python check_sheets.py

pause
