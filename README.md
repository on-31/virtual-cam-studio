# 🎥 Virtual Cam Studio (Sanal Kamera Stüdyosu)

<p align="center">
  <b>Seçtiğiniz fotoğraf ve videoları sanal web kamerasına yansıtan modern masaüstü uygulaması.</b><br>
  <i>Stream any photo or video directly to your virtual webcam for Zoom, Discord, Google Meet, Skype, and Web Browsers.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.12-brightgreen.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License">
</p>

---

## 🇹🇷 Türkçe Açıklama

Bu uygulama, bilgisayarınızda seçtiğiniz herhangi bir **fotoğrafı** veya **videoyu** gerçek bir web kamerası akışı gibi Windows'a tanıtır. Böylece karşı taraf sizin gerçek kameranız yerine seçtiğiniz medyayı görür.

### ✨ Başlıca Özellikler
- **Desteklenen Formatlar:**
  - 🖼️ **Fotoğraflar:** JPG, PNG, WEBP, BMP, TIFF
  - 🎬 **Videolar:** MP4, MKV, AVI, MOV, WEBM, WMV
- **Canlı Önizleme:** Kameraya yansıtılan kareyi arayüzde gerçek zamanlı izleyin.
- **Video Kontrolleri:**
  - Video zaman çubuğu (timeline) ile ileri-geri sarma.
  - Oynat / Duraklat ve Başa Sar.
  - 🔄 **Otomatik Döngü (Loop):** Video bitince kesintisiz baştan başlar.
  - Oynatma Hızı: `0.5x`, `1.0x`, `1.5x`, `2.0x`.
- **Görüntü Modları:**
  - **En-Boy Koru (Fit):** Oranı bozmadan ortalar, kenarları siyah bırakır.
  - **Bulanık Arka Plan (Blur Fit):** Sosyal medya ve TV tarzı şık bulanık arka plan.
  - **Doldur / Kırp (Fill):** 16:9 kamera alanını tamamen doldurur.
  - **Esnet (Stretch):** Çerçeveye esnetir.
- **Efektler:** Yatay çevirme (Ayna Modu), dikey çevirme, parlaklık ve kontrast ayarları.
- **Çözünürlük:** 1080p Full HD, 720p HD, 480p SD (30 & 60 FPS).
- **Sürücü Desteği:** OBS Virtual Camera DirectShow filtreleri paket içerisindedir, tam OBS Studio kurulumu gerektirmez.

---

## 🇬🇧 English Description

A lightweight, modern Windows desktop application that streams any selected image or video to a virtual webcam device, allowing you to use custom media as your camera feed in Zoom, Discord, Google Meet, Skype, Teams, and web browsers.

### Key Features
- **Media Formats:** JPG, PNG, WEBP, BMP, MP4, MKV, AVI, MOV, WEBM.
- **Playback Engine:** Play/Pause, timeline scrubber, repeat loop, speed multipliers (0.5x to 2.0x).
- **Framing Modes:** Aspect Fit (black borders), Blur Background (cinematic fill), Crop to Fill (16:9), and Stretch.
- **Webcam FX:** Horizontal flip (mirror mode), vertical flip, brightness and contrast sliders.
- **Embedded Driver:** Includes OBS Virtual Camera DirectShow module for 1-click registration without full OBS installation.

---

## 🚀 Kurulum ve Çalıştırma (How to Run)

### Seçenek 1: Kaynak Koddan Çalıştırma (Python ile)
Gereksinimleri yükleyin ve başlatın:
```bash
pip install customtkinter opencv-python pillow pyvirtualcam
python main.py
```

### Seçenek 2: Tek Tıkla Başlatıcı
- Klasördeki `run.bat` dosyasına çift tıklayarak hemen açabilirsiniz.

---

## 📜 Lisans
Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynaklı olarak paylaşılmıştır.
