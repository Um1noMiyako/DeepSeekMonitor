@echo off
chcp 65001 >nul
echo ========================================
echo   DeepSeek Monitor -- PyInstaller 打包
echo ========================================
echo.

cd /d "%~dp0"

pyinstaller ^
  --name "DeepSeekMonitor" ^
  --onefile ^
  --windowed ^
  --icon resources/icon.png ^
  --add-data "resources;resources" ^
  --hidden-import PySide6.QtNetwork ^
  --hidden-import cryptography.fernet ^
  --hidden-import cryptography.hazmat.primitives ^
  --hidden-import cryptography.hazmat.backends ^
  --clean ^
  main.py

echo.
echo ========================================
echo   打包完成！产物在 dist\DeepSeekMonitor.exe
echo ========================================
pause
