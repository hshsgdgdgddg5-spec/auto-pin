import os
import time
import requests
import json
import base64
import subprocess
import tempfile

PINTEREST_API_BASE = "https://api.pinterest.com/v5"
PINTEREST_SANDBOX_BASE = "https://api-sandbox.pinterest.com/v5"
PINTEREST_OAUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"

def extract_cover_image(video_path):
    """Videonun 1. saniyesinden kapak resmi çıkarıp base64 döndürür, çıkaramazsa keyframe 0 kullanır"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [
            "ffmpeg", "-y",
            "-ss", "00:00:01",
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "2",
            tmp_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if res.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100:
            with open(tmp_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return {
                "cover_image_content_type": "image/jpeg",
                "cover_image_data": b64
            }
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    except Exception:
        pass

    # Fallback: Pinterest'in videodan 0. saniyedeki kareyi otomatik alması için
    return {
        "cover_image_key_frame_time": 0
    }

class PinterestClient:
    def __init__(self, access_token=None, use_sandbox=False):
        self.access_token = access_token.strip() if access_token else ""
        self.use_sandbox = use_sandbox
        self.api_base = PINTEREST_SANDBOX_BASE if use_sandbox else PINTEREST_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json"
        }

    def check_permissions(self):
        """Token'ın video ve pin oluşturma (pins:write) iznine sahip olup olmadığını doğrular"""
        if not self.access_token:
            return False, "Token girilmemiş."
        try:
            res = requests.post(
                f"{self.api_base}/media",
                headers=self.headers,
                json={"media_type": "video"},
                timeout=10
            )
            if res.status_code in [200, 201]:
                return True, "Video paylaşma yetkisi (pins:write) onaylandı."
            if "pins:write" in res.text or res.status_code == 401:
                return False, "Tokeninizde 'pins:write' (Video & Pin Paylaşma) yetkisi EKSİK! Lütfen Pinterest Developers sayfasından token oluştururken 'pins:write' kutucuğunu işaretleyin."
            return True, "OK"
        except Exception as e:
            return True, str(e)

    def is_connected(self):
        """Gerçek Pinterest hesabının bağlı olup olmadığını doğrular"""
        if not self.access_token:
            return False, "Pinterest Access Token girilmemiş veya hesap bağlı değil."

        try:
            res = requests.get(
                f"{self.api_base}/user_account",
                headers=self.headers,
                timeout=12
            )
            if res.status_code == 200:
                user_data = res.json()
                return True, {
                    "username": user_data.get("username", "Kullanıcı"),
                    "business_name": user_data.get("business_name") or user_data.get("username", "Pinterest Hesabı"),
                    "profile_image": user_data.get("profile_image", ""),
                    "account_type": user_data.get("account_type", "BUSINESS"),
                    "has_write_permission": True,
                    "permission_warning": "",
                    "is_sandbox": self.use_sandbox
                }
            elif res.status_code == 401:
                return False, "Access Token geçersiz veya süresi dolmuş. Lütfen hesabı tekrar bağlayın."
            else:
                return False, f"Pinterest API Hatası ({res.status_code}): {res.text}"
        except Exception as e:
            return False, f"Pinterest bağlantı hatası: {str(e)}"

    def get_boards(self):
        """Kullanıcının gerçek Pinterest panolarını çeker"""
        if not self.access_token:
            return []

        try:
            res = requests.get(
                f"{self.api_base}/boards?page_size=100",
                headers=self.headers,
                timeout=12
            )
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                return [{"id": b["id"], "name": b["name"]} for b in items]
            else:
                print(f"Panolar alınamadı: {res.status_code} - {res.text}")
                return []
        except Exception as e:
            print(f"Pano listesi çekme hatası: {e}")
            return []

    def create_board_if_not_exists(self, board_name="Sosyal"):
        """Eğer belirtilen pano yoksa Pinterest'te yeni pano oluşturur"""
        boards = self.get_boards()
        for b in boards:
            if b["name"].lower() == board_name.lower():
                return b["id"]

        try:
            res = requests.post(
                f"{self.api_base}/boards",
                headers=self.headers,
                json={"name": board_name, "privacy": "PUBLIC"},
                timeout=12
            )
            if res.status_code in [200, 201]:
                return res.json().get("id")
        except Exception as e:
            print(f"Pano oluşturma hatası: {e}")
        return None

    def upload_video_pin(self, video_path, title, description, link, board_id):
        """
        Pinterest API v5 ile Video Pin Paylaşımı
        """
        if not self.access_token:
            return False, "Pinterest hesabınız bağlı değil! Lütfen önce sağ üstteki 'Pinterest Hesabını Bağla' butonuna tıklayarak hesabınızı bağlayın."

        if not os.path.exists(video_path):
            return False, f"Video dosyası diskte bulunamadı: {video_path}"

        # Board ID kontrolü veya adı eşleme
        if not board_id:
            boards = self.get_boards()
            if boards:
                board_id = boards[0]["id"]
            else:
                board_id = self.create_board_if_not_exists("Sosyal")
                if not board_id:
                    return False, "Pinterest panosu bulunamadı. Lütfen ayarlardan bir pano seçin."

        try:
            # 1. ADIM: Pinterest API'den video yükleme yetkisi al (POST /v5/media)
            reg_res = requests.post(
                f"{self.api_base}/media",
                headers=self.headers,
                json={"media_type": "video"},
                timeout=15
            )

            if reg_res.status_code not in [200, 201]:
                err_details = reg_res.text
                return False, f"Pinterest video yükleme kaydı oluşturulamadı ({reg_res.status_code}): {err_details}"

            reg_data = reg_res.json()
            media_id = reg_data.get("media_id")
            upload_url = reg_data.get("upload_url")
            upload_params = reg_data.get("upload_parameters", {})

            if not upload_url or not media_id:
                return False, f"Pinterest sunucusundan yükleme adresi alınamadı: {reg_res.text}"

            # 2. ADIM: Videoyu Pinterest'in S3 depolama sunucusuna yükle
            with open(video_path, "rb") as f:
                filename = os.path.basename(video_path)
                files = {"file": (filename, f, "video/mp4")}
                upload_res = requests.post(
                    upload_url,
                    data=upload_params,
                    files=files,
                    timeout=180
                )

                if upload_res.status_code not in [200, 204]:
                    return False, f"Video Pinterest S3 sunucusuna yüklenemedi ({upload_res.status_code}): {upload_res.text}"

            # 3. ADIM: Pinterest'in videoyu işlemesini bekle (GET /v5/media/{media_id})
            max_attempts = 25
            media_ready = False
            for attempt in range(max_attempts):
                time.sleep(3)
                stat_res = requests.get(
                    f"{self.api_base}/media/{media_id}",
                    headers=self.headers,
                    timeout=12
                )
                if stat_res.status_code == 200:
                    stat_data = stat_res.json()
                    status = stat_data.get("status")
                    if status == "succeeded":
                        media_ready = True
                        break
                    elif status == "failed":
                        return False, f"Pinterest videoyu işleyemedi (failed). Video formatı veya süresi uygun olmayabilir."
                elif stat_res.status_code == 401:
                    return False, "Oturum süresi doldu. Lütfen Pinterest hesabınızı tekrar bağlayın."

            if not media_ready:
                return False, "Pinterest video işleme süresi zaman aşımına uğradı (60+ sn)."

            # 4. ADIM: Pin'i Pinterest hesabında oluştur (POST /v5/pins)
            media_source_data = {
                "source_type": "video_id",
                "media_id": media_id
            }
            # Pinterest video pinleri için kapak resmi bilgisi zorunludur:
            cover_params = extract_cover_image(video_path)
            media_source_data.update(cover_params)

            pin_payload = {
                "title": title[:100] if title else "Yeni Ürün Tanıtımı",
                "description": description[:500] if description else "",
                "board_id": board_id,
                "media_source": media_source_data
            }
            if link and link.strip():
                pin_payload["link"] = link.strip()

            pin_res = requests.post(
                f"{self.api_base}/pins",
                headers=self.headers,
                json=pin_payload,
                timeout=20
            )

            if pin_res.status_code in [200, 201]:
                pin_data = pin_res.json()
                pin_id = pin_data.get("id")
                pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
                return True, {
                    "id": pin_id,
                    "url": pin_url,
                    "title": title,
                    "board_id": board_id
                }
            elif pin_res.status_code == 403 and "Trial access" in pin_res.text:
                return False, (
                    "Pinterest 'Trial Access' Kısıtlaması (Hata 29):\n"
                    "Uygulamanız şu an Pinterest'te 'Deneme (Trial)' aşamasında olduğu için canlı pin paylaşımına izin verilmiyor.\n\n"
                    "👉 ÇÖZÜM:\n"
                    "1) developers.pinterest.com/apps adresine gidin ve uygulamanızı seçin.\n"
                    "2) 'Upgrade to Standard Access' (Standart Erişime Yükselt) butonuna tıklayın ve 1 dakikalık onay formunu doldurun.\n"
                    "3) Veya hemen test etmek için sağ üstteki Ayarlar'dan 'Sandbox (Test) Modu'nu açabilirsiniz."
                )
            else:
                return False, f"Pinterest Pin oluşturulamadı ({pin_res.status_code}): {pin_res.text}"

        except requests.exceptions.RequestException as e:
            return False, f"Pinterest sunucusuyla iletişim hatası: {str(e)}"
        except Exception as e:
            return False, f"Beklenmeyen paylaşım hatası: {str(e)}"

        except requests.exceptions.RequestException as e:
            return False, f"Pinterest sunucusuyla iletişim hatası: {str(e)}"
        except Exception as e:
            return False, f"Beklenmeyen paylaşım hatası: {str(e)}"

    @staticmethod
    def get_oauth_url(client_id, redirect_uri):
        """Kullanıcının Pinterest ile oturum açması için resmi OAuth bağlantısı"""
        scopes = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
        return f"{PINTEREST_OAUTH_URL}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}"

    @staticmethod
    def exchange_code_for_token(client_id, client_secret, code, redirect_uri):
        """OAuth kodunu Access Token ile takas eder"""
        try:
            auth = (str(client_id).strip(), str(client_secret).strip())
            data = {
                "grant_type": "authorization_code",
                "code": code.strip(),
                "redirect_uri": redirect_uri.strip()
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            res = requests.post(PINTEREST_TOKEN_URL, data=data, auth=auth, headers=headers, timeout=15)
            if res.status_code == 200:
                token_data = res.json()
                return True, token_data
            else:
                return False, f"Token takası başarısız ({res.status_code}): {res.text}"
        except Exception as e:
            return False, f"OAuth hatası: {str(e)}"
