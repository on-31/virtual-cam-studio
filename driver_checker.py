"""
driver_checker.py
Sanal kamera sürücüsünün (OBS Virtual Camera) sistemde kurulu olup olmadığını kontrol eder.
Gerekli DLL dosyalarını otomatik olarak kalıcı bir konuma (%LOCALAPPDATA%\\VirtualCamStudio\\driver)
yerleştirir ve tek tıkla Windows'a kaydeder.
"""

import sys
import subprocess
import os
import shutil
import ctypes
from pathlib import Path

def get_base_dir():
    """PyInstaller _MEIPASS veya normal çalışma dizinini döner."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def get_permanent_driver_dir():
    """DLL'lerin kalıcı olarak barınacağı AppData dizini."""
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    p = Path(local_app_data) / "VirtualCamStudio" / "driver"
    p.mkdir(parents=True, exist_ok=True)
    return p

def ensure_driver_files():
    """
    Uygulama içine paketlenmiş obs-virtualcam DLL'lerini
    kalıcı AppData dizinine kopyalar.
    """
    perm_dir = get_permanent_driver_dir()
    base_dir = get_base_dir()
    src_driver_dir = base_dir / "driver"

    copied = False
    for dll_name in ["obs-virtualcam-module64.dll", "obs-virtualcam-module32.dll"]:
        src_file = src_driver_dir / dll_name
        # Eğer driver klasöründe değilse doğrudan ana dizine de bak
        if not src_file.exists():
            src_file = base_dir / dll_name

        dest_file = perm_dir / dll_name
        if src_file.exists():
            if not dest_file.exists() or dest_file.stat().st_size != src_file.stat().st_size:
                shutil.copy2(src_file, dest_file)
                copied = True
    return perm_dir

def is_camera_available():
    """
    Sanal kamera hazır mı kontrol eder.
    Dönüş: (bool: hazir_mi, str: aciklama_veya_aygit_adi)
    """
    try:
        import pyvirtualcam
        with pyvirtualcam.Camera(width=320, height=240, fps=15) as cam:
            return True, str(cam.device)
    except RuntimeError as e:
        err_str = str(e)
        return False, err_str
    except Exception as e:
        return False, str(e)

def register_driver_elevated():
    """
    Windows UAC onay penceresi açarak kalıcı dizindeki DLL'leri
    regsvr32 ile DirectShow filtresi olarak kaydeder.
    """
    perm_dir = ensure_driver_files()
    dll64 = perm_dir / "obs-virtualcam-module64.dll"
    dll32 = perm_dir / "obs-virtualcam-module32.dll"

    if not dll64.exists():
        return False, "Sanal kamera DLL dosyası bulunamadı."

    # Kurulum için geçici bir .cmd dosyası oluşturalım
    cmd_script = perm_dir / "install.cmd"
    script_content = f"""@echo off
regsvr32.exe /i /s "{dll64}"
if exist "{dll32}" regsvr32.exe /i /s "{dll32}"
exit /b
"""
    with open(cmd_script, "w", encoding="utf-8") as f:
        f.write(script_content)

    try:
        # ShellExecuteW ile 'runas' (Yönetici Olarak Çalıştır)
        res = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            "cmd.exe",
            f'/c "{cmd_script}"',
            None,
            0  # SW_HIDE (arka planda sessiz çalışsın)
        )
        if res > 32:
            return True, "Sürücü başarıyla aktifleştirildi."
        else:
            return False, f"Yönetici izni verilmedi veya hata oluştu (Kod: {res})."
    except Exception as e:
        return False, f"Hata: {str(e)}"
