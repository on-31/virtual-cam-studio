@echo off
chcp 65001 >nul
echo ========================================================
echo   Sanal Kamera Sürücüsü Kurulumu (OBS Virtual Camera)
echo ========================================================
echo.

:: Yönetici kontrolü
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [UYARI] Yönetici hakları gerekiyor!
    echo Yönetici izni penceresi açılıyor...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~dp0install_camera_driver.bat\"' -Verb RunAs"
    exit /b
)

set OBS_PKG_DIR=%LOCALAPPDATA%\Microsoft\WinGet\Packages\OBSProject.OBSStudio_Microsoft.Winget.Source_8wekyb3d8bbwe\core\win-dshow\data

if exist "%OBS_PKG_DIR%\obs-virtualcam-module64.dll" (
    echo 64-bit Sanal Kamera DLL bulundu, sisteme kaydediliyor...
    regsvr32.exe /i /s "%OBS_PKG_DIR%\obs-virtualcam-module64.dll"
    if exist "%OBS_PKG_DIR%\obs-virtualcam-module32.dll" (
        regsvr32.exe /i /s "%OBS_PKG_DIR%\obs-virtualcam-module32.dll"
    )
    echo [BAŞARILI] OBS Sanal Kamera başarıyla Windows'a kaydedildi!
    echo Zoom, Discord, Google Meet, Skype ve tarayıcılarda 'OBS Virtual Camera' olarak görünecektir.
) else (
    echo [HATA] OBS Virtual Camera DLL dosyası bulunamadı.
    echo Lütfen OBS Studio'yu kurduğunuzdan emin olun.
)

echo.
echo Devam etmek için bir tuşa basın...
pause >nul
