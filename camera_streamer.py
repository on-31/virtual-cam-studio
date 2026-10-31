"""
camera_streamer.py
Sanal kameraya arka plan iş parçacığında (thread) kareler gönderen yayın motoru.
"""

import threading
import time
import numpy as np
import pyvirtualcam

class CameraStreamer:
    STATUS_STOPPED = "STOPPED"
    STATUS_STARTING = "STARTING"
    STATUS_STREAMING = "STREAMING"
    STATUS_ERROR = "ERROR"

    def __init__(self, media_player, on_status_change=None, on_preview_frame=None):
        self.media_player = media_player
        self.on_status_change = on_status_change
        self.on_preview_frame = on_preview_frame
        
        self.width = 1280
        self.height = 720
        self.fps = 30
        
        self.status = self.STATUS_STOPPED
        self.device_name = ""
        self.error_message = ""
        
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def set_resolution(self, width, height, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.media_player.set_target_resolution(width, height)

    def is_streaming(self):
        return self.status == self.STATUS_STREAMING

    def start(self):
        """Yayını başlatır."""
        with self._lock:
            if self.status == self.STATUS_STREAMING or (self._thread and self._thread.is_alive()):
                return
            
            self._set_status(self.STATUS_STARTING, "Sanal kamera başlatılıyor...")
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Yayını durdurur."""
        with self._lock:
            if self.status == self.STATUS_STOPPED:
                return
            self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            
        self._set_status(self.STATUS_STOPPED, "Yayın durduruldu.")

    def _set_status(self, status, message=""):
        self.status = status
        self.error_message = message if status == self.STATUS_ERROR else ""
        if self.on_status_change:
            try:
                self.on_status_change(status, message)
            except Exception as e:
                print(f"Status callback hatası: {e}")

    def _run_loop(self):
        """Arka plan yayın döngüsü."""
        cam = None
        try:
            # pyvirtualcam kamerayı açar
            cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.RGB
            )
            self.device_name = str(cam.device)
            self._set_status(self.STATUS_STREAMING, f"Yayında: {self.device_name}")
            
            last_preview_time = 0.0
            preview_interval = 1.0 / 30.0  # Önizleme için max 30 fps

            while not self._stop_event.is_set():
                t0 = time.time()
                
                # Kareyi medyadan çek
                frame = self.media_player.read_next_frame()
                if frame is None or frame.shape[0] != self.height or frame.shape[1] != self.width:
                    # Uygun boyutta değilse boyutlandır
                    frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

                # Sanal kameraya gönder
                cam.send(frame)
                
                # Önizleme callback'i (GUI için)
                now = time.time()
                if now - last_preview_time >= preview_interval:
                    last_preview_time = now
                    if self.on_preview_frame:
                        try:
                            self.on_preview_frame(frame)
                        except Exception:
                            pass
                
                # FPS uyutması
                cam.sleep_until_next_frame()

        except RuntimeError as e:
            err = str(e)
            if "device not found" in err.lower() or "no camera registered" in err.lower():
                msg = "Sanal kamera aygıtı bulunamadı. Lütfen OBS Virtual Camera veya UnityCapture kurun."
            else:
                msg = f"Kamera hatası: {err}"
            self._set_status(self.STATUS_ERROR, msg)
        except Exception as e:
            self._set_status(self.STATUS_ERROR, f"Beklenmeyen hata: {str(e)}")
        finally:
            if cam:
                try:
                    cam.close()
                except Exception:
                    pass
            if self.status != self.STATUS_ERROR:
                self._set_status(self.STATUS_STOPPED, "Yayın sonlandı.")
