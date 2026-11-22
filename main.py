import os
import uvicorn
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Replit Web Sunucusu Başlatılıyor (Port: {port})...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
