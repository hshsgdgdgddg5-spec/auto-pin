import os
import shutil
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from database import (
    init_db, get_all_settings, set_setting, get_videos,
    get_video_by_id, add_video, update_video, delete_video,
    get_recent_logs, add_log
)
from automation import engine
from pinterest_client import PinterestClient
from ai_generator import generate_product_content, clean_filename_to_product

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "data", "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Veritabanını başlat
init_db()

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- Sayfa Yönlendirmeleri ---
async def homepage(request):
    index_file = os.path.join(BASE_DIR, "templates", "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

# --- API Yönlendirmeleri ---
async def get_status(request):
    status_data = engine.get_status()
    settings = get_all_settings()
    use_sandbox = settings.get("use_sandbox", "false").lower() == "true"
    client = PinterestClient(access_token=settings.get("pinterest_access_token"), use_sandbox=use_sandbox)
    is_connected, acc_info = client.is_connected()
    
    status_data["account_connected"] = is_connected
    status_data["account_info"] = acc_info if is_connected else None
    return JSONResponse(status_data)

async def get_pinterest_boards(request):
    settings = get_all_settings()
    use_sandbox = settings.get("use_sandbox", "false").lower() == "true"
    client = PinterestClient(access_token=settings.get("pinterest_access_token"), use_sandbox=use_sandbox)
    boards = client.get_boards()
    return JSONResponse({"boards": boards})

async def connect_pinterest_api(request):
    data = await request.json()
    token = data.get("access_token", "").strip()
    if not token:
        return JSONResponse({"success": False, "message": "Lütfen Pinterest Access Token girin."}, status_code=400)
    
    settings = get_all_settings()
    use_sandbox = settings.get("use_sandbox", "false").lower() == "true"
    client = PinterestClient(access_token=token, use_sandbox=use_sandbox)
    connected, info = client.is_connected()
    if not connected:
        return JSONResponse({"success": False, "message": f"Bağlantı başarısız: {info}"}, status_code=400)
    
    if not info.get("has_write_permission", True):
        return JSONResponse({
            "success": False,
            "message": f"DİKKAT: Hesabınız doğrulandı ancak VİDEO PAYLAŞMA YETKİSİ ('pins:write') EKSİK!\n\nLütfen developers.pinterest.com/apps adresine gidin, token üretirken 'pins:write' kutucuğunu işaretleyin ve yeni tokenı yapıştırın."
        }, status_code=400)
    
    set_setting("pinterest_access_token", token)
    username = info.get("business_name") or info.get("username", "")
    set_setting("pinterest_account_name", username)
    
    # Gerçek panoları çek
    boards = client.get_boards()
    selected_board = None
    if boards:
        # Önceden seçili yoksa 'Sosyal' panosunu veya ilk panoyu seç
        selected_board = next((b for b in boards if b["name"].lower() == "sosyal"), boards[0])
        set_setting("pinterest_board_id", selected_board["id"])
        set_setting("pinterest_board_name", selected_board["name"])

    add_log(f"Pinterest hesabı başarıyla bağlandı: @{info.get('username')}", "SUCCESS")
    return JSONResponse({
        "success": True,
        "message": f"Tebrikler! @{info.get('username')} hesabı başarıyla bağlandı.",
        "user": info,
        "boards": boards,
        "selected_board": selected_board
    })

async def oauth_login(request):
    app_id = request.query_params.get("app_id", "").strip()
    app_secret = request.query_params.get("app_secret", "").strip()
    if app_id:
        set_setting("pinterest_app_id", app_id)
    if app_secret:
        set_setting("pinterest_app_secret", app_secret)

    settings = get_all_settings()
    app_id = settings.get("pinterest_app_id", "").strip()
    if not app_id:
        return HTMLResponse("<script>alert('Lütfen App ID (Client ID) girin.'); window.location.href='/';</script>")

    host = request.headers.get("host", "localhost:8080")
    proto = request.headers.get("x-forwarded-proto")
    scheme = proto if proto else ("https" if ("onrender.com" in host or "railway" in host) else "http")
    redirect_uri = f"{scheme}://{host}/oauth/callback"

    url = PinterestClient.get_oauth_url(app_id, redirect_uri)
    return RedirectResponse(url)

async def oauth_callback(request):
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    error_desc = request.query_params.get("error_description", "")

    if error:
        return HTMLResponse(f"""
        <body style="font-family:sans-serif; background:#0f172a; color:#fff; padding:40px; text-align:center;">
            <h2 style="color:#f43f5e;">Yetkilendirme İptal Edildi veya Hata Oluştu</h2>
            <p>{error}: {error_desc}</p>
            <br>
            <a href="/" style="display:inline-block; padding:10px 20px; background:#e60023; color:#fff; border-radius:10px; text-decoration:none; font-weight:bold;">Panele Geri Dön</a>
        </body>
        """)

    if not code:
        return HTMLResponse("OAuth yetkilendirme kodu bulunamadı.", status_code=400)

    settings = get_all_settings()
    app_id = settings.get("pinterest_app_id", "").strip()
    app_secret = settings.get("pinterest_app_secret", "").strip()

    host = request.headers.get("host", "localhost:8080")
    proto = request.headers.get("x-forwarded-proto")
    scheme = proto if proto else ("https" if ("onrender.com" in host or "railway" in host) else "http")
    redirect_uri = f"{scheme}://{host}/oauth/callback"

    ok, token_data = PinterestClient.exchange_code_for_token(app_id, app_secret, code, redirect_uri)
    if ok:
        token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")
        set_setting("pinterest_access_token", token)
        if refresh_token:
            set_setting("pinterest_refresh_token", refresh_token)

        # Kullanıcı bilgilerini ve panoları doğrudan Pinterest'ten çek
        client = PinterestClient(access_token=token)
        connected, info = client.is_connected()
        if connected:
            set_setting("pinterest_account_name", info.get("business_name") or info.get("username", ""))
            boards = client.get_boards()
            if boards:
                target = next((b for b in boards if b["name"].lower() == "sosyal"), boards[0])
                set_setting("pinterest_board_id", target["id"])
                set_setting("pinterest_board_name", target["name"])

        add_log("Tebrikler! Pinterest hesabı resmi Authorize yöntemiyle bağlandı!", "SUCCESS")
        return RedirectResponse("/?authorized=1")
    else:
        return HTMLResponse(f"""
        <body style="font-family:sans-serif; background:#0f172a; color:#fff; padding:40px; text-align:center;">
            <h2 style="color:#f43f5e;">Yetkilendirme Hatası</h2>
            <p style="background:#1e293b; padding:15px; border-radius:10px; display:inline-block; max-width:600px; word-break:break-word;">{token_data}</p>
            <p style="color:#94a3b8; font-size:13px; margin-top:20px;">
                Lütfen App ID ve App Secret bilgilerinizin doğruluğunu ve Pinterest Developers sayfasında Redirect URI olarak 
                <br><strong style="color:#38bdf8;">{redirect_uri}</strong> eklendiğini kontrol edin.
            </p>
            <br>
            <a href="/" style="display:inline-block; padding:10px 20px; background:#e60023; color:#fff; border-radius:10px; text-decoration:none; font-weight:bold;">Panele Geri Dön</a>
        </body>
        """, status_code=400)

async def get_settings_api(request):
    return JSONResponse(get_all_settings())

async def save_settings_api(request):
    data = await request.json()
    for key, val in data.items():
        set_setting(key, val)
    add_log("Ayarlar güncellendi.", "INFO")
    return JSONResponse({"success": True, "message": "Ayarlar başarıyla kaydedildi."})

async def list_videos(request):
    videos = get_videos()
    return JSONResponse(videos)

async def upload_videos(request):
    form = await request.form()
    files = form.getlist("files")
    if not files:
        return JSONResponse({"success": False, "message": "Yüklenecek dosya seçilmedi."}, status_code=400)

    settings = get_all_settings()
    uploaded_count = 0

    for upload_file in files:
        filename = upload_file.filename
        if not filename:
            continue
        
        filepath = os.path.join(VIDEOS_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)

        filesize = os.path.getsize(filepath)
        product_name = clean_filename_to_product(filename)

        # Otomatik AI içerik üret
        ai_data = generate_product_content(product_name, settings.get("gemini_api_key"))

        add_video(
            filename=filename,
            filepath=filepath,
            filesize=filesize,
            product_name=product_name,
            title=ai_data["title"],
            description=ai_data["description"],
            link=settings.get("default_link", ""),
            board_id=settings.get("pinterest_board_id", ""),
            board_name=settings.get("pinterest_board_name", "Sosyal"),
            tags=ai_data["tags"]
        )
        uploaded_count += 1

    add_log(f"{uploaded_count} yeni video yüklendi ve kuyruğa eklendi.", "INFO")
    return JSONResponse({"success": True, "message": f"{uploaded_count} video başarıyla yüklendi ve sıraya alındı."})

async def scan_folder(request):
    data = await request.json()
    folder_path = data.get("folder_path", "").strip()

    if not folder_path or not os.path.exists(folder_path):
        return JSONResponse({"success": False, "message": "Belirtilen klasör yolu bulunamadı."}, status_code=400)

    settings = get_all_settings()
    valid_exts = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    added_count = 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_exts:
                src_path = os.path.join(root, file)
                filesize = os.path.getsize(src_path)
                product_name = clean_filename_to_product(file)
                
                # Hedef klasöre kopyala veya doğrudan referans ver
                dest_path = os.path.join(VIDEOS_DIR, file)
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
                
                ai_data = generate_product_content(product_name, settings.get("gemini_api_key"))

                add_video(
                    filename=file,
                    filepath=dest_path,
                    filesize=filesize,
                    product_name=product_name,
                    title=ai_data["title"],
                    description=ai_data["description"],
                    link=settings.get("default_link", ""),
                    board_id=settings.get("pinterest_board_id", ""),
                    board_name=settings.get("pinterest_board_name", "Sosyal"),
                    tags=ai_data["tags"]
                )
                added_count += 1

    add_log(f"Klasörden ({folder_path}) {added_count} video sıraya eklendi.", "INFO")
    return JSONResponse({"success": True, "message": f"{added_count} video klasörden başarıyla eklendi."})

async def share_video_now(request):
    video_id = int(request.path_params["id"])
    success, res = engine.share_single_video(video_id)
    if success:
        return JSONResponse({"success": True, "result": res})
    else:
        return JSONResponse({"success": False, "message": str(res)}, status_code=400)

async def generate_video_ai(request):
    video_id = int(request.path_params["id"])
    video = get_video_by_id(video_id)
    if not video:
        return JSONResponse({"success": False, "message": "Video bulunamadı."}, status_code=404)

    settings = get_all_settings()
    product_name = video.get("product_name") or clean_filename_to_product(video["filename"])
    ai_data = generate_product_content(product_name, settings.get("gemini_api_key"))

    update_video(
        video_id,
        title=ai_data["title"],
        description=ai_data["description"],
        tags=ai_data["tags"],
        product_name=product_name
    )

    add_log(f"Video #{video_id} ({product_name}) için AI içerikleri yenilendi.", "INFO")
    return JSONResponse({"success": True, "data": ai_data})

async def update_video_api(request):
    video_id = int(request.path_params["id"])
    data = await request.json()
    update_video(video_id, **data)
    add_log(f"Video #{video_id} bilgileri güncellendi.", "INFO")
    return JSONResponse({"success": True, "message": "Video güncellendi."})

async def delete_video_api(request):
    video_id = int(request.path_params["id"])
    delete_video(video_id)
    add_log(f"Video #{video_id} kuyruktan silindi.", "INFO")
    return JSONResponse({"success": True, "message": "Video silindi."})

async def preview_ai(request):
    data = await request.json()
    product_name = data.get("product_name", "")
    settings = get_all_settings()
    res = generate_product_content(product_name, settings.get("gemini_api_key"))
    return JSONResponse(res)

async def start_auto(request):
    success, msg = engine.start()
    return JSONResponse({"success": success, "message": msg})

async def stop_auto(request):
    success, msg = engine.stop()
    return JSONResponse({"success": success, "message": msg})

async def get_logs_api(request):
    logs = get_recent_logs(40)
    return JSONResponse(logs)

# --- Routes Tanımı ---
routes = [
    Route("/", homepage),
    Route("/oauth/pinterest/login", oauth_login),
    Route("/oauth/callback", oauth_callback),
    Route("/api/status", get_status, methods=["GET"]),
    Route("/api/settings", get_settings_api, methods=["GET"]),
    Route("/api/settings", save_settings_api, methods=["POST"]),
    Route("/api/pinterest/connect", connect_pinterest_api, methods=["POST"]),
    Route("/api/pinterest/boards", get_pinterest_boards, methods=["GET"]),
    Route("/api/videos", list_videos, methods=["GET"]),
    Route("/api/videos/upload", upload_videos, methods=["POST"]),
    Route("/api/videos/scan-folder", scan_folder, methods=["POST"]),
    Route("/api/videos/{id:int}/share", share_video_now, methods=["POST"]),
    Route("/api/videos/{id:int}/generate-ai", generate_video_ai, methods=["POST"]),
    Route("/api/videos/{id:int}", update_video_api, methods=["PUT"]),
    Route("/api/videos/{id:int}", delete_video_api, methods=["DELETE"]),
    Route("/api/ai/preview", preview_ai, methods=["POST"]),
    Route("/api/automation/start", start_auto, methods=["POST"]),
    Route("/api/automation/stop", stop_auto, methods=["POST"]),
    Route("/api/logs", get_logs_api, methods=["GET"]),
    Mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Server başlatılıyor: http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
