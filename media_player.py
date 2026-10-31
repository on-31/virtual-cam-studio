"""
media_player.py
Fotoğraf ve video dosyalarını okuyan, ölçekleyen ve sanal kamera için
RGB formatında kareler (frame) üreten medya motoru.
"""

import cv2
import numpy as np
from PIL import Image, ImageOps
import os
import time

class MediaPlayer:
    def __init__(self, target_width=1280, target_height=720):
        self.target_width = target_width
        self.target_height = target_height
        
        self.file_path = None
        self.is_video = False
        self.is_loaded = False
        
        # Video oynatma durumu
        self.cap = None
        self.total_frames = 0
        self.native_fps = 30.0
        self.duration_sec = 0.0
        self.current_frame_idx = 0
        self.is_playing = True
        self.loop = True
        self.playback_speed = 1.0
        
        # Fotoğraf verisi
        self.image_rgb = None
        
        # Efekt ve ölçekleme ayarları
        self.scale_mode = "fit"  # "fit", "fill", "stretch", "fit_blur"
        self.mirror_h = False
        self.mirror_v = False
        self.brightness = 0       # -100 to +100
        self.contrast = 1.0       # 0.5 to 2.0
        
        # Son üretilen kare önbelleği
        self.last_frame = None
        self.last_frame_time = 0.0

    def load_media(self, path):
        """Fotoğraf veya video dosyasını yükler."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dosya bulunamadı: {path}")
            
        self.close()
        self.file_path = path
        
        ext = os.path.splitext(path)[1].lower()
        image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".m4v"}
        
        if ext in image_exts:
            self._load_image(path)
        elif ext in video_exts:
            self._load_video(path)
        else:
            # Uzantı bilinmiyorsa önce video olarak açmayı dene, olmazsa resim dene
            try:
                self._load_video(path)
            except Exception:
                self._load_image(path)
                
        self.is_loaded = True
        self.last_frame = self.get_current_frame()
        return self.is_video

    def _load_image(self, path):
        self.is_video = False
        # PIL ile açıp EXIF oryantasyonunu düzeltelim
        pil_img = Image.open(path)
        pil_img = ImageOps.exif_transpose(pil_img)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        self.image_rgb = np.array(pil_img)
        self.total_frames = 1
        self.duration_sec = 0.0
        self.native_fps = 30.0

    def _load_video(self, path):
        self.is_video = True
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Video dosyası açılamadı: {path}")
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.native_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.native_fps <= 0 or np.isnan(self.native_fps):
            self.native_fps = 30.0
        self.duration_sec = self.total_frames / self.native_fps if self.total_frames > 0 else 0
        self.current_frame_idx = 0
        self.is_playing = True

    def set_target_resolution(self, width, height):
        self.target_width = width
        self.target_height = height
        if self.is_loaded:
            self.last_frame = self.get_current_frame()

    def play(self):
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def toggle_play(self):
        self.is_playing = not self.is_playing
        return self.is_playing

    def seek_ratio(self, ratio):
        """0.0 ile 1.0 arasında bir konuma gider."""
        if not self.is_video or not self.cap or self.total_frames <= 0:
            return
        target_frame = int(np.clip(ratio, 0.0, 1.0) * (self.total_frames - 1))
        self.seek_frame(target_frame)

    def seek_frame(self, frame_idx):
        if not self.is_video or not self.cap:
            return
        self.current_frame_idx = int(np.clip(frame_idx, 0, max(0, self.total_frames - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_idx)
        ret, bgr_frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            self.last_frame = self._process_frame(rgb_frame)

    def read_next_frame(self):
        """
        Bir sonraki kareyi okur ve döndürür (RGB uint8 numpy array).
        Video duraklatılmışsa veya resimse mevcut kareyi döner.
        """
        if not self.is_loaded:
            # Boş siyah ekran döner
            return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

        if not self.is_video:
            return self._process_frame(self.image_rgb)

        if not self.is_playing:
            if self.last_frame is not None:
                return self.last_frame
            # İlk kareyi oku
            ret, bgr_frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                self.last_frame = self._process_frame(rgb)
                return self.last_frame
            return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

        # Video oynatılıyor
        ret, bgr_frame = self.cap.read()
        if not ret:
            # Video bitti
            if self.loop and self.total_frames > 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_idx = 0
                ret, bgr_frame = self.cap.read()
            else:
                self.is_playing = False
                return self.last_frame if self.last_frame is not None else np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

        if ret:
            self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            self.last_frame = self._process_frame(rgb)
            return self.last_frame

        return self.last_frame

    def get_current_frame(self):
        """Mevcut son işlenmiş kareyi döndürür."""
        if self.last_frame is not None:
            return self.last_frame
        return self.read_next_frame()

    def _process_frame(self, frame_rgb):
        """Ölçekleme, ayna ve renk efektlerini uygular."""
        if frame_rgb is None:
            return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

        # 1. Oryantasyon / Ayna
        processed = frame_rgb
        if self.mirror_h and self.mirror_v:
            processed = cv2.flip(processed, -1)
        elif self.mirror_h:
            processed = cv2.flip(processed, 1)
        elif self.mirror_v:
            processed = cv2.flip(processed, 0)

        # 2. Parlaklık & Kontrast
        if self.contrast != 1.0 or self.brightness != 0:
            # output = contrast * input + brightness
            processed = cv2.convertScaleAbs(processed, alpha=self.contrast, beta=self.brightness)

        # 3. Ölçekleme & Hedef Çözünürlüğe Oturtma
        h, w = processed.shape[:2]
        tw, th = self.target_width, self.target_height

        if self.scale_mode == "stretch":
            return cv2.resize(processed, (tw, th), interpolation=cv2.INTER_LINEAR)

        elif self.scale_mode == "fill":
            # Hedef alanı tamamen dolduracak şekilde büyüt ve ortadan kırp
            scale = max(tw / w, th / h)
            nw, nh = int(round(w * scale)), int(round(h * scale))
            resized = cv2.resize(processed, (nw, nh), interpolation=cv2.INTER_LINEAR)
            
            x1 = (nw - tw) // 2
            y1 = (nh - th) // 2
            return resized[y1:y1+th, x1:x1+tw]

        elif self.scale_mode == "fit_blur":
            # Bulanık arka plan + ortalanmış net görsel (TV tarzı)
            bg = cv2.resize(processed, (tw, th), interpolation=cv2.INTER_LINEAR)
            bg = cv2.GaussianBlur(bg, (51, 51), 0)
            
            scale = min(tw / w, th / h)
            nw, nh = int(round(w * scale)), int(round(h * scale))
            resized = cv2.resize(processed, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            
            x1 = (tw - nw) // 2
            y1 = (th - nh) // 2
            bg[y1:y1+nh, x1:x1+nw] = resized
            return bg

        else:  # "fit" (siyah kenarlıklar ile en-boy oranını koru)
            canvas = np.zeros((th, tw, 3), dtype=np.uint8)
            scale = min(tw / w, th / h)
            nw, nh = int(round(w * scale)), int(round(h * scale))
            resized = cv2.resize(processed, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            
            x1 = (tw - nw) // 2
            y1 = (th - nh) // 2
            canvas[y1:y1+nh, x1:x1+nw] = resized
            return canvas

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.image_rgb = None
        self.is_loaded = False
        self.last_frame = None
