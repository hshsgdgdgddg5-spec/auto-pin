import time
import threading
from datetime import datetime
from database import (
    get_setting, set_setting, get_next_pending_video,
    update_video, add_log, get_all_settings
)
from pinterest_client import PinterestClient
from ai_generator import generate_product_content, clean_filename_to_product

class AutomationEngine:
    def __init__(self):
        self.thread = None
        self.is_running = False
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            if self.is_running:
                return False, "Otomasyon zaten çalışıyor."

            token = get_setting("pinterest_access_token", "").strip()
            if not token:
                return False, "Pinterest hesabınız bağlı değil! Lütfen önce 'Pinterest Hesabını Bağla' butonuna tıklayarak hesabınızı bağlayın."

            self.is_running = True
            set_setting("automation_status", "running")
            add_log("Otomasyon başlatıldı. Her 1 dakikada bir video sırayla Pinterest hesabınızda paylaşılacak.", "INFO")
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            return True, "Otomasyon başarıyla başlatıldı. Videolarınız her 1 dakikada sırayla paylaşılacaktır."

    def stop(self):
        with self.lock:
            if not self.is_running:
                return False, "Otomasyon zaten durdurulmuş."
            self.is_running = False
            set_setting("automation_status", "stopped")
            add_log("Otomasyon durduruldu.", "WARNING")
            return True, "Otomasyon durduruldu."

    def get_status(self):
        return {
            "is_running": self.is_running,
            "status": "running" if self.is_running else "stopped"
        }

    def share_single_video(self, video_id):
        """Tek bir videoyu anında paylaşır (Hemen Paylaş Butonu)"""
        from database import get_video_by_id
        video = get_video_by_id(video_id)
        if not video:
            return False, "Video bulunamadı."
        
        return self._process_video(video)

    def _process_video(self, video):
        settings = get_all_settings()
        video_id = video["id"]
        update_video(video_id, status="processing")
        
        prod = clean_filename_to_product(video["filename"])
        product_name = video.get("product_name") or (prod[0] if isinstance(prod, tuple) else prod)
        title = video.get("title")
        description = video.get("description")
        tags = video.get("tags")
        link = video.get("link") or settings.get("default_link", "")
        board_id = video.get("board_id") or settings.get("pinterest_board_id", "")

        # Eğer başlık/açıklama boşsa otomatik yapay zeka ile ürüne özel üret
        if not title or not description or not tags:
            add_log(f"[{product_name}] için yapay zeka ile ürüne özel başlık ve etiketler üretiliyor...", "INFO")
            ai_data = generate_product_content(
                video["filename"],
                api_key=settings.get("gemini_api_key"),
                video_id=video_id,
                video_path=video.get("filepath")
            )
            title = ai_data["title"]
            description = ai_data["description"]
            tags = ai_data["tags"]
            if ai_data.get("product_name"):
                product_name = ai_data["product_name"]
            update_video(video_id, title=title, description=description, tags=tags, product_name=product_name)

        add_log(f"Video Pinterest'e yükleniyor: '{title}'", "INFO")
        use_sandbox = settings.get("use_sandbox", "false").lower() == "true"
        client = PinterestClient(access_token=settings.get("pinterest_access_token"), use_sandbox=use_sandbox)
        
        success, result = client.upload_video_pin(
            video_path=video["filepath"],
            title=title,
            description=description,
            link=link,
            board_id=board_id
        )

        if success:
            pin_id = result.get("id", "")
            pin_url = result.get("url", "")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_video(
                video_id,
                status="completed",
                pin_id=pin_id,
                pin_url=pin_url,
                published_at=now_str,
                error_message=""
            )
            add_log(f"BAŞARILI: '{title}' Pinterest'te paylaşıldı! Pin URL: {pin_url}", "SUCCESS")
            return True, result
        else:
            err_msg = str(result)
            update_video(video_id, status="failed", error_message=err_msg)
            add_log(f"HATA: '{title}' paylaşılamadı: {err_msg}", "ERROR")
            return False, err_msg

    def _run_loop(self):
        add_log("Otomasyon arka plan servisi aktif edildi. Kuyruk taranıyor...", "INFO")
        while self.is_running:
            try:
                video = get_next_pending_video()
                if video:
                    add_log(f"Sıradaki video alınıyor: #{video['id']} - {video.get('product_name', video['filename'])}", "INFO")
                    self._process_video(video)
                else:
                    add_log("Sırada bekleyen video kalmadı. Yeni video eklenene kadar bekleniyor...", "INFO")

                # Bekleme süresi (Varsayılan 1 dakika = 60 saniye)
                interval_minutes = float(get_setting("interval_minutes", "1"))
                wait_seconds = max(10, int(interval_minutes * 60))
                add_log(f"Sonraki paylaşım için {int(interval_minutes)} dakika ({wait_seconds} saniye) bekleniyor...", "INFO")

                for _ in range(wait_seconds):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                add_log(f"Otomasyon döngüsünde hata: {str(e)}", "ERROR")
                time.sleep(10)

# Global motor örneği
engine = AutomationEngine()
