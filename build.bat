@echo off
chcp 65001 >nul 2>&1
title Sonar Vice Widget - EXE Build
color 0F

echo.
echo  ====================================================
echo     Sonar Vice Widget - EXE Olusturucu
echo  ====================================================
echo.

:: Python kontrolu
echo  [1/4] Python kontrol ediliyor...

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  [!] Python bulunamadi. Python 3.10+ yukleyin.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo        %PYVER% bulundu.

:: Bagimliliklar
echo.
echo  [2/4] Bagimliliklar kuruluyor...
cd /d "%~dp0"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet
echo        Hazir.

:: Icon
echo.
echo  [3/4] Icon olusturuluyor...
python gen_icon.py

:: Build
echo.
echo  [4/4] EXE olusturuluyor (1-2 dakika surebilir)...
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "SonarViceWidget" ^
    --icon "assets/icon.ico" ^
    --add-data "config.py;." ^
    --add-data "api;api" ^
    --add-data "ui;ui" ^
    --hidden-import "pywintypes" ^
    --hidden-import "win32gui" ^
    --hidden-import "win32con" ^
    --hidden-import "win32api" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "customtkinter" ^
    --collect-data "customtkinter" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo  [!] Build basarisiz oldu.
    pause
    exit /b 1
)

:: Temizlik
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0SonarViceWidget.spec" del "%~dp0SonarViceWidget.spec"

echo.
echo  ====================================================
echo     Build tamamlandi!
echo  ====================================================
echo.
echo  EXE: dist\SonarViceWidget.exe
echo  NOT: SteelSeries GG kurulu olmalidir.
echo  ====================================================
echo.

explorer "%~dp0dist"
pause
