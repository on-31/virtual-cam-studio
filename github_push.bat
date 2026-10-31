@echo off
chcp 65001 >nul
title GitHub'a Otomatik Yükleyici

echo ========================================================
echo        Sanal Kamera Stüdyosu - GitHub Yükleyici
echo ========================================================
echo.
echo 1. https://github.com/new adresine gidin.
echo 2. Repository name olarak 'virtual-cam-studio' yazın ve Create repository deyin.
echo 3. Oluşan repo linkini (örn: https://github.com/kullanici/virtual-cam-studio.git) kopyalayın.
echo.
set /p REPO_URL="Repo Linkinizi Buraya Yapıştırın ve Enter'a basın: "

if "%REPO_URL%"=="" (
    echo Repo linki girmediniz! Çıkılıyor...
    pause
    exit /b
)

set GIT_EXE="C:\Program Files\Git\cmd\git.exe"

echo.
echo Git deposu hazırlanıyor...
cd /d "%~dp0"
%GIT_EXE% init -b main
%GIT_EXE% config user.name "VirtualCamStudio"
%GIT_EXE% config user.email "virtualcam@users.noreply.github.com"
%GIT_EXE% add .
%GIT_EXE% commit -m "feat: Sanal Kamera Stüdyosu ilk sürüm v1.0.0"
%GIT_EXE% remote remove origin >nul 2>&1
%GIT_EXE% remote add origin %REPO_URL%
%GIT_EXE% branch -M main

echo.
echo Kodlar GitHub'a gönderiliyor...
%GIT_EXE% push -u origin main

if %errorLevel% equ 0 (
    echo.
    echo [BAŞARILI] Tüm kodlar başarıyla GitHub'a yüklendi!
) else (
    echo.
    echo [BİLGİ] Eğer giriş yapmanız istendiyse ekrandaki tarayıcı onayını verin.
)

echo.
pause
