"""
main.py
Sanal Kamera Stüdyosu (Virtual Camera Studio)
Seçtiğiniz fotoğraf ve videoları sanal web kamerasına yansıtır.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np

# Modüllerimizi içe aktaralım
from media_player import MediaPlayer
from camera_streamer import CameraStreamer
import driver_checker

# CustomTkinter Teması
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VirtualCamApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sanal Kamera Stüdyosu - Medyayı Kameraya Yansıtıcı")
        self.geometry("1100x720")
        self.minsize(980, 640)

        # İkonu ayarla
        try:
            icon_p = driver_checker.get_base_dir() / "icon.ico"
            if icon_p.exists():
                self.iconbitmap(str(icon_p))
        except Exception:
            pass

        # Medya ve Yayın motorları
        self.media_player = MediaPlayer(target_width=1280, target_height=720)
        self.streamer = CameraStreamer(
            media_player=self.media_player,
            on_status_change=self.on_streamer_status,
            on_preview_frame=self.on_streamer_frame
        )

        # Önizleme ve arayüz durumu
        self.is_slider_dragging = False
        self.driver_available = False
        self.driver_name = ""
        self.current_preview_photo = None
        self.preview_canvas_width = 640
        self.preview_canvas_height = 360

        # Arayüzü oluştur
        self._build_ui()

        # Paketlenmiş sürücü DLL dosyalarını kalıcı konuma yerleştir
        try:
            driver_checker.ensure_driver_files()
        except Exception as e:
            print("Sürücü hazırlama uyarısı:", e)

        # Kamera sürücü durumunu kontrol et
        self.check_driver_status()

        # Önizleme yenileme döngüsünü başlat (Yayın dururken video oynatımı için)
        self.after(33, self._local_preview_loop)

        # Pencere kapatılınca kaynakları temizle
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Ana grid yerleşimi (Sol: Önizleme + Oynatıcı, Sağ: Medya + Ayarlar + Yayın)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ==============================================================
        # SOL PANEL: ÖNİZLEME & OYNATICI
        # ==============================================================
        left_frame = ctk.CTkFrame(self, corner_radius=12)
        left_frame.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)

        # Başlık ve Durum Rozeti
        top_bar = ctk.CTkFrame(left_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="🎥 Canlı Kamera Önizlemesi",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        self.status_badge = ctk.CTkLabel(
            top_bar,
            text="🔴 Çevrimdışı (Yayın Kapalı)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#331111",
            text_color="#ff5555",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.status_badge.grid(row=0, column=1, sticky="e")

        # Önizleme Ekranı (Canvas)
        preview_container = ctk.CTkFrame(left_frame, fg_color="#101014", corner_radius=10)
        preview_container.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        preview_container.grid_columnconfigure(0, weight=1)
        preview_container.grid_rowconfigure(0, weight=1)

        self.preview_canvas = tk.Canvas(
            preview_container,
            bg="#121216",
            highlightthickness=0,
            bd=0
        )
        self.preview_canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.preview_canvas.bind("<Configure>", self._on_canvas_resize)

        # Video Zaman Çubuğu & Bilgisi
        self.controls_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1)

        self.time_lbl = ctk.CTkLabel(
            self.controls_frame,
            text="00:00 / 00:00",
            font=ctk.CTkFont(size=12, family="Consolas")
        )
        self.time_lbl.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.timeline_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0.0,
            to=1.0,
            command=self._on_slider_change
        )
        self.timeline_slider.set(0.0)
        self.timeline_slider.grid(row=0, column=1, sticky="ew")
        self.timeline_slider.bind("<ButtonPress-1>", lambda e: setattr(self, 'is_slider_dragging', True))
        self.timeline_slider.bind("<ButtonRelease-1>", self._on_slider_release)

        # Oynatma Butonları Satırı
        playback_btn_row = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        playback_btn_row.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        self.btn_play_pause = ctk.CTkButton(
            playback_btn_row,
            text="⏸ Duraklat",
            width=110,
            command=self.toggle_play_pause
        )
        self.btn_play_pause.pack(side="left", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            playback_btn_row,
            text="⏹ Başa Sar",
            width=90,
            fg_color="#3a3a44",
            hover_color="#4f4f5a",
            command=self.stop_and_rewind
        )
        self.btn_stop.pack(side="left", padx=8)

        self.loop_switch = ctk.CTkSwitch(
            playback_btn_row,
            text="🔄 Otomatik Tekrarla (Döngü)",
            command=self._on_loop_toggle
        )
        self.loop_switch.select()
        self.loop_switch.pack(side="left", padx=16)

        # Hız Seçici
        speed_lbl = ctk.CTkLabel(playback_btn_row, text="Hız:", font=ctk.CTkFont(size=12))
        speed_lbl.pack(side="left", padx=(10, 4))
        self.speed_combo = ctk.CTkComboBox(
            playback_btn_row,
            values=["0.5x", "1.0x", "1.5x", "2.0x"],
            width=80,
            command=self._on_speed_change
        )
        self.speed_combo.set("1.0x")
        self.speed_combo.pack(side="left")

        # ==============================================================
        # SAĞ PANEL: MEDYA SEÇİMİ, EFEKTLER & YAYIN
        # ==============================================================
        right_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        right_frame.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)

        # 1. Medya Seçim Kartı
        section_media = ctk.CTkFrame(right_frame, fg_color="#1e1e24", corner_radius=10)
        section_media.pack(fill="x", pady=(0, 12), padx=4)

        sec_title = ctk.CTkLabel(
            section_media,
            text="📁 Medya Kaynağı Seç",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        sec_title.pack(anchor="w", padx=14, pady=(12, 6))

        btn_row = ctk.CTkFrame(section_media, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=6)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_choose_photo = ctk.CTkButton(
            btn_row,
            text="🖼️ Fotoğraf Seç",
            height=38,
            fg_color="#2b5278",
            hover_color="#366899",
            command=self.choose_photo
        )
        self.btn_choose_photo.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_choose_video = ctk.CTkButton(
            btn_row,
            text="🎬 Video Seç",
            height=38,
            fg_color="#70369d",
            hover_color="#8942bf",
            command=self.choose_video
        )
        self.btn_choose_video.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Seçili dosya bilgisi
        self.file_info_lbl = ctk.CTkLabel(
            section_media,
            text="Henüz dosya seçilmedi\nDesteklenenler: JPG, PNG, WEBP, MP4, MKV, AVI",
            font=ctk.CTkFont(size=12),
            text_color="#999999",
            justify="center"
        )
        self.file_info_lbl.pack(fill="x", padx=14, pady=(4, 14))

        # 2. Görüntü & Yerleşim Ayarları
        section_display = ctk.CTkFrame(right_frame, fg_color="#1e1e24", corner_radius=10)
        section_display.pack(fill="x", pady=8, padx=4)

        sec_title2 = ctk.CTkLabel(
            section_display,
            text="🎨 Görüntü & Yerleşim Modu",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        sec_title2.pack(anchor="w", padx=14, pady=(12, 8))

        scale_lbl = ctk.CTkLabel(section_display, text="Ölçekleme:", font=ctk.CTkFont(size=13))
        scale_lbl.pack(anchor="w", padx=14, pady=(0, 2))

        self.scale_mode_combo = ctk.CTkComboBox(
            section_display,
            values=[
                "En-Boy Koru (Siyah Kenarlık)",
                "Bulanık Arka Plan (Blur Fit)",
                "Doldur / Kırp (Fill/Crop)",
                "Esnet (Stretch)"
            ],
            command=self._on_scale_mode_change
        )
        self.scale_mode_combo.set("En-Boy Koru (Siyah Kenarlık)")
        self.scale_mode_combo.pack(fill="x", padx=14, pady=(0, 10))

        # Ayna Modu (Flip)
        flip_row = ctk.CTkFrame(section_display, fg_color="transparent")
        flip_row.pack(fill="x", padx=14, pady=(0, 10))

        self.mirror_h_switch = ctk.CTkSwitch(
            flip_row,
            text="↔ Yatay Çevir (Ayna Modu)",
            command=self._on_mirror_toggle
        )
        self.mirror_h_switch.pack(side="left", padx=(0, 10))

        self.mirror_v_switch = ctk.CTkSwitch(
            flip_row,
            text="↕ Dikey Çevir",
            command=self._on_mirror_toggle
        )
        self.mirror_v_switch.pack(side="left")

        # Parlaklık & Kontrast
        adjust_frame = ctk.CTkFrame(section_display, fg_color="transparent")
        adjust_frame.pack(fill="x", padx=14, pady=(0, 12))
        adjust_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(adjust_frame, text="Parlaklık:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=4)
        self.brightness_slider = ctk.CTkSlider(adjust_frame, from_=-80, to=80, command=self._on_color_adjust)
        self.brightness_slider.set(0)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        ctk.CTkLabel(adjust_frame, text="Kontrast:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", pady=4)
        self.contrast_slider = ctk.CTkSlider(adjust_frame, from_=0.5, to=1.8, command=self._on_color_adjust)
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        # 3. Sanal Kamera & Yayın Kontrolü
        section_cam = ctk.CTkFrame(right_frame, fg_color="#1e1e24", corner_radius=10)
        section_cam.pack(fill="x", pady=8, padx=4)

        sec_title3 = ctk.CTkLabel(
            section_cam,
            text="⚡ Sanal Kamera Ayarları",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        sec_title3.pack(anchor="w", padx=14, pady=(12, 8))

        # Çözünürlük ve FPS
        res_row = ctk.CTkFrame(section_cam, fg_color="transparent")
        res_row.pack(fill="x", padx=14, pady=(0, 10))
        res_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(res_row, text="Çözünürlük:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(res_row, text="FPS:", font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="w")

        self.res_combo = ctk.CTkComboBox(
            res_row,
            values=["1920x1080 (Full HD)", "1280x720 (HD)", "640x480 (SD)"],
            command=self._on_resolution_change
        )
        self.res_combo.set("1280x720 (HD)")
        self.res_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(2, 0))

        self.fps_combo = ctk.CTkComboBox(
            res_row,
            values=["30 FPS", "60 FPS", "20 FPS"],
            command=self._on_resolution_change
        )
        self.fps_combo.set("30 FPS")
        self.fps_combo.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(2, 0))

        # Sürücü Durum Kartı
        self.driver_status_frame = ctk.CTkFrame(section_cam, fg_color="#272730", corner_radius=8)
        self.driver_status_frame.pack(fill="x", padx=14, pady=8)

        self.driver_status_lbl = ctk.CTkLabel(
            self.driver_status_frame,
            text="Sanal kamera durumu kontrol ediliyor...",
            font=ctk.CTkFont(size=12),
            wraplength=340
        )
        self.driver_status_lbl.pack(padx=10, pady=8)

        self.btn_install_driver = ctk.CTkButton(
            self.driver_status_frame,
            text="⚙️ Sanal Kamera Sürücüsünü Kur (1 Tıkla)",
            fg_color="#b85d19",
            hover_color="#d66e20",
            command=self.install_driver_clicked
        )
        # Varsayılan gizli, sürücü yoksa gösterilecek

        # BÜYÜK YAYIN BAŞLAT BUTONU
        self.btn_toggle_stream = ctk.CTkButton(
            section_cam,
            text="🚀 KAMERAYA YANSITMAYI BAŞLAT",
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f8b4c",
            hover_color="#28aa5d",
            command=self.toggle_streaming
        )
        self.btn_toggle_stream.pack(fill="x", padx=14, pady=(12, 16))

    # ==============================================================
    # MEDYA VE OYNATICI FONKSİYONLARI
    # ==============================================================
    def choose_photo(self):
        filetypes = [
            ("Fotoğraf Dosyaları", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
            ("Tüm Dosyalar", "*.*")
        ]
        path = filedialog.askopenfilename(title="Fotoğraf Seçin", filetypes=filetypes)
        if path:
            self._load_file(path)

    def choose_video(self):
        filetypes = [
            ("Video Dosyaları", "*.mp4 *.mkv *.avi *.mov *.webm *.wmv"),
            ("Tüm Dosyalar", "*.*")
        ]
        path = filedialog.askopenfilename(title="Video Seçin", filetypes=filetypes)
        if path:
            self._load_file(path)

    def _load_file(self, path):
        try:
            is_vid = self.media_player.load_media(path)
            fname = os.path.basename(path)
            
            if is_vid:
                dur_str = time.strftime('%M:%S', time.gmtime(self.media_player.duration_sec))
                fps = int(round(self.media_player.native_fps))
                info_text = f"🎬 {fname}\nSüre: {dur_str} | Kare Hızı: {fps} FPS"
                self.controls_frame.grid()
                self.btn_play_pause.configure(text="⏸ Duraklat")
            else:
                h, w = self.media_player.image_rgb.shape[:2]
                info_text = f"🖼️ {fname}\nÇözünürlük: {w}x{h} px"
                self.time_lbl.configure(text="Fotoğraf")
                self.timeline_slider.set(0.0)

            self.file_info_lbl.configure(text=info_text, text_color="#ffffff")
            self._update_preview_display(self.media_player.get_current_frame())

        except Exception as e:
            messagebox.showerror("Medya Yükleme Hatası", f"Dosya açılamadı:\n{str(e)}")

    def toggle_play_pause(self):
        if not self.media_player.is_loaded or not self.media_player.is_video:
            return
        is_playing = self.media_player.toggle_play()
        self.btn_play_pause.configure(text="⏸ Duraklat" if is_playing else "▶ Oynat")

    def stop_and_rewind(self):
        if not self.media_player.is_loaded or not self.media_player.is_video:
            return
        self.media_player.seek_frame(0)
        self.timeline_slider.set(0.0)
        self._update_preview_display(self.media_player.get_current_frame())

    def _on_loop_toggle(self):
        self.media_player.loop = self.loop_switch.get() == 1

    def _on_speed_change(self, choice):
        speed_map = {"0.5x": 0.5, "1.0x": 1.0, "1.5x": 1.5, "2.0x": 2.0}
        self.media_player.playback_speed = speed_map.get(choice, 1.0)

    def _on_slider_change(self, value):
        if self.is_slider_dragging and self.media_player.is_video:
            # Slider kaydırılırken anlık konumu göster
            cur_sec = value * self.media_player.duration_sec
            tot_sec = self.media_player.duration_sec
            cur_str = time.strftime('%M:%S', time.gmtime(cur_sec))
            tot_str = time.strftime('%M:%S', time.gmtime(tot_sec))
            self.time_lbl.configure(text=f"{cur_str} / {tot_str}")

    def _on_slider_release(self, event):
        self.is_slider_dragging = False
        if self.media_player.is_video:
            val = self.timeline_slider.get()
            self.media_player.seek_ratio(val)
            self._update_preview_display(self.media_player.get_current_frame())

    def _on_scale_mode_change(self, choice):
        mode_map = {
            "En-Boy Koru (Siyah Kenarlık)": "fit",
            "Bulanık Arka Plan (Blur Fit)": "fit_blur",
            "Doldur / Kırp (Fill/Crop)": "fill",
            "Esnet (Stretch)": "stretch"
        }
        self.media_player.scale_mode = mode_map.get(choice, "fit")
        if self.media_player.is_loaded:
            self._update_preview_display(self.media_player.get_current_frame())

    def _on_mirror_toggle(self):
        self.media_player.mirror_h = self.mirror_h_switch.get() == 1
        self.media_player.mirror_v = self.mirror_v_switch.get() == 1
        if self.media_player.is_loaded:
            self._update_preview_display(self.media_player.get_current_frame())

    def _on_color_adjust(self, val):
        self.media_player.brightness = int(self.brightness_slider.get())
        self.media_player.contrast = float(self.contrast_slider.get())
        if self.media_player.is_loaded:
            self._update_preview_display(self.media_player.get_current_frame())

    def _on_resolution_change(self, val=None):
        res_str = self.res_combo.get()
        if "1920x1080" in res_str:
            w, h = 1920, 1080
        elif "640x480" in res_str:
            w, h = 640, 480
        else:
            w, h = 1280, 720

        fps_str = self.fps_combo.get()
        fps = 30
        if "60" in fps_str:
            fps = 60
        elif "20" in fps_str:
            fps = 20

        self.streamer.set_resolution(w, h, fps)

    # ==============================================================
    # SÜRÜCÜ & YAYIN YÖNETİMİ
    # ==============================================================
    def check_driver_status(self):
        """OBS Virtual Camera sürücüsünü sorgular."""
        ok, msg = driver_checker.is_camera_available()
        self.driver_available = ok
        if ok:
            self.driver_name = msg
            self.driver_status_lbl.configure(
                text=f"✅ Sanal Kamera Hazır: {msg}",
                text_color="#66ff88"
            )
            self.btn_install_driver.pack_forget()
        else:
            self.driver_status_lbl.configure(
                text="⚠️ Sanal Kamera Sürücüsü Henüz Kayıtlı Değil!\n(Kamerayı kullanmak için aşağıdaki butona basın)",
                text_color="#ffbb44"
            )
            self.btn_install_driver.pack(fill="x", padx=10, pady=(0, 8))

    def install_driver_clicked(self):
        """Kullanıcı butona bastığında Windows UAC ile kurulumu çalıştırır."""
        ok, msg = driver_checker.register_driver_elevated()
        if ok:
            messagebox.showinfo(
                "Sürücü Kurulumu",
                "Yönetici onay penceresi açıldı.\nLütfen ekranda çıkan Windows onayına 'Evet' deyin.\nOnay verdikten sonra 'Tamam'a basarak devam edin."
            )
            # Birkaç saniye içinde durumu tekrar kontrol et
            self.after(1000, self.check_driver_status)
            self.after(3000, self.check_driver_status)
        else:
            messagebox.showerror("Kurulum Başlatılamadı", msg)

    def toggle_streaming(self):
        if self.streamer.is_streaming():
            self.streamer.stop()
            self.btn_toggle_stream.configure(
                text="🚀 KAMERAYA YANSITMAYI BAŞLAT",
                fg_color="#1f8b4c",
                hover_color="#28aa5d"
            )
        else:
            if not self.media_player.is_loaded:
                messagebox.showwarning("Medya Seçilmedi", "Lütfen önce kameraya yansıtmak istediğiniz bir fotoğraf veya video seçin.")
                return

            self._on_resolution_change()
            self.streamer.start()

    def on_streamer_status(self, status, message):
        """Streamer thread'inden gelen durum güncellemeleri."""
        def _update():
            if status == CameraStreamer.STATUS_STREAMING:
                self.status_badge.configure(
                    text="🟢 CANLI YAYINDA (Kamera Aktif)",
                    fg_color="#113318",
                    text_color="#55ff88"
                )
                self.btn_toggle_stream.configure(
                    text="⏹ YAYINI DURDUR",
                    fg_color="#a82323",
                    hover_color="#c83030"
                )
            elif status == CameraStreamer.STATUS_ERROR:
                self.status_badge.configure(
                    text="❌ Kamera Hatası",
                    fg_color="#331111",
                    text_color="#ff5555"
                )
                self.btn_toggle_stream.configure(
                    text="🚀 KAMERAYA YANSITMAYI BAŞLAT",
                    fg_color="#1f8b4c",
                    hover_color="#28aa5d"
                )
                messagebox.showerror("Sanal Kamera Hatası", message)
                self.check_driver_status()
            else:
                self.status_badge.configure(
                    text="🔴 Çevrimdışı (Yayın Kapalı)",
                    fg_color="#331111",
                    text_color="#ff5555"
                )
                self.btn_toggle_stream.configure(
                    text="🚀 KAMERAYA YANSITMAYI BAŞLAT",
                    fg_color="#1f8b4c",
                    hover_color="#28aa5d"
                )
        self.after(0, _update)

    def on_streamer_frame(self, frame_rgb):
        """Streamer çalışırken anlık kareyi önizleme penceresine basar."""
        self.after(0, lambda: self._update_preview_display(frame_rgb))

    # ==============================================================
    # ÖNİZLEME DÖNGÜSÜ & ÇİZİM
    # ==============================================================
    def _local_preview_loop(self):
        """Yayın kapalıyken bile videonun arayüzde oynatılmasını sağlar."""
        if not self.streamer.is_streaming() and self.media_player.is_loaded and self.media_player.is_video and self.media_player.is_playing:
            frame = self.media_player.read_next_frame()
            self._update_preview_display(frame)
            
            # Zaman göstergesini güncelle
            if not self.is_slider_dragging and self.media_player.total_frames > 0:
                ratio = self.media_player.current_frame_idx / self.media_player.total_frames
                self.timeline_slider.set(ratio)
                cur_sec = ratio * self.media_player.duration_sec
                tot_sec = self.media_player.duration_sec
                cur_str = time.strftime('%M:%S', time.gmtime(cur_sec))
                tot_str = time.strftime('%M:%S', time.gmtime(tot_sec))
                self.time_lbl.configure(text=f"{cur_str} / {tot_str}")

        # Yaklaşık 30 FPS hızında tekrar çağır
        self.after(33, self._local_preview_loop)

    def _on_canvas_resize(self, event):
        self.preview_canvas_width = max(100, event.width)
        self.preview_canvas_height = max(100, event.height)
        if self.media_player.is_loaded:
            self._update_preview_display(self.media_player.get_current_frame())
        else:
            self._draw_placeholder()

    def _draw_placeholder(self):
        cw, ch = self.preview_canvas_width, self.preview_canvas_height
        self.preview_canvas.delete("all")
        self.preview_canvas.create_rectangle(0, 0, cw, ch, fill="#121216", outline="")
        self.preview_canvas.create_text(
            cw // 2,
            ch // 2 - 20,
            text="📷",
            font=("Segoe UI Emoji", 48),
            fill="#444455"
        )
        self.preview_canvas.create_text(
            cw // 2,
            ch // 2 + 40,
            text="Lütfen Sağ Panelden Fotoğraf veya Video Seçin",
            font=("Segoe UI", 13),
            fill="#888899"
        )

    def _update_preview_display(self, frame_rgb):
        if frame_rgb is None:
            self._draw_placeholder()
            return

        cw, ch = self.preview_canvas_width, self.preview_canvas_height
        fh, fw = frame_rgb.shape[:2]
        
        # En boy oranını koruyarak canvas içine oturt
        scale = min(cw / fw, ch / fh)
        dw = max(1, int(round(fw * scale)))
        dh = max(1, int(round(fh * scale)))
        
        resized = cv2.resize(frame_rgb, (dw, dh), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
        img_pil = Image.fromarray(resized)
        self.current_preview_photo = ImageTk.PhotoImage(img_pil)

        self.preview_canvas.delete("all")
        # Merkeze yerleştir
        self.preview_canvas.create_image(
            cw // 2,
            ch // 2,
            image=self.current_preview_photo,
            anchor="center"
        )

    def on_close(self):
        """Pencere kapatıldığında temizlik."""
        try:
            self.streamer.stop()
            self.media_player.close()
        except Exception:
            pass
        self.destroy()

if __name__ == "__main__":
    app = VirtualCamApp()
    app.mainloop()
