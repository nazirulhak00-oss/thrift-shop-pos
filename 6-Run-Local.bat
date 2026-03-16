@echo off
chcp 65001 >nul
title Thrift Shop POS - Local Test
color 0E

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   🚀 รันแอป Thrift Shop POS (Local)             ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ไม่พบ Python!
    pause
    exit /b 1
)

echo ✅ พบ Python แล้ว
echo.

REM ตรวจสอบ Streamlit
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo ⚠️ ไม่พบ Streamlit กำลังติดตั้ง...
    pip install streamlit plotly -q
)

REM ตรวจสอบ secrets.toml
if not exist ".streamlit\secrets.toml" (
    echo.
    echo ❌ ไม่พบไฟล์ .streamlit\secrets.toml
    echo.
    echo 💡 กรุณารัน: 1-Setup-Secrets.bat ก่อน
    echo    เพื่อสร้างไฟล์ตั้งค่าการเชื่อมต่อ
    echo.
    pause
    exit /b 1
)

echo ✅ พบไฟล์ secrets.toml แล้ว
echo.
echo 🌐 กำลังเปิดแอป...
echo    URL: http://localhost:8501
echo.
echo ⚠️ อย่าปิดหน้าต่างนี้! (แอปจะหยุดทำงาน)
echo    ต้องการหยุด: กด Ctrl+C
echo.
echo ════════════════════════════════════════════════════
echo.

streamlit run app.py

pause
