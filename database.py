import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "pinterest_auto.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Videos / Queue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER DEFAULT 0,
            product_name TEXT DEFAULT '',
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            link TEXT DEFAULT '',
            board_id TEXT DEFAULT '',
            board_name TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
            error_message TEXT DEFAULT '',
            pin_id TEXT DEFAULT '',
            pin_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    """)

    # Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT DEFAULT 'INFO',
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Default settings
    default_settings = {
        "interval_minutes": "1",
        "pinterest_access_token": "",
        "pinterest_refresh_token": "",
        "pinterest_app_id": "",
        "pinterest_app_secret": "",
        "pinterest_account_name": "",
        "pinterest_board_id": "",
        "pinterest_board_name": "Sosyal",
        "default_link": "https://findesdecks.com/searchPage?title=Shop%20Now",
        "gemini_api_key": "",
        "automation_status": "stopped", # stopped, running
        "auto_generate_ai": "true",
        "use_sandbox": "false"
    }

    for key, val in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def get_all_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def add_log(message, level="INFO"):
    conn = get_db()
    conn.execute("INSERT INTO logs (level, message, created_at) VALUES (?, ?, ?)", 
                 (level, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_recent_logs(limit=30):
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_video(filename, filepath, filesize=0, product_name="", title="", description="", link="", board_id="", board_name="", tags=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO videos (filename, filepath, filesize, product_name, title, description, link, board_id, board_name, tags, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (filename, filepath, filesize, product_name, title, description, link, board_id, board_name, tags))
    conn.commit()
    video_id = cursor.lastrowid
    conn.close()
    return video_id

def get_videos(status=None):
    conn = get_db()
    if status:
        rows = conn.execute("SELECT * FROM videos WHERE status = ? ORDER BY id ASC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM videos ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_video_by_id(video_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_video(video_id, **kwargs):
    conn = get_db()
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(video_id)
    query = f"UPDATE videos SET {', '.join(fields)} WHERE id = ?"
    conn.execute(query, tuple(values))
    conn.commit()
    conn.close()

def delete_video(video_id):
    conn = get_db()
    video = get_video_by_id(video_id)
    if video and os.path.exists(video.get("filepath", "")):
        try:
            os.remove(video["filepath"])
        except Exception:
            pass
    conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()

def delete_videos_bulk(video_ids=None, delete_all=False, status=None):
    """Toplu video silme fonksiyonu: veritabanından ve diskten siler"""
    conn = get_db()
    cursor = conn.cursor()
    deleted_count = 0
    
    if delete_all:
        rows = cursor.execute("SELECT id, filepath FROM videos").fetchall()
        for r in rows:
            if r["filepath"] and os.path.exists(r["filepath"]):
                try:
                    os.remove(r["filepath"])
                except Exception:
                    pass
        cursor.execute("DELETE FROM videos")
        deleted_count = len(rows)
    elif status:
        rows = cursor.execute("SELECT id, filepath FROM videos WHERE status = ?", (status,)).fetchall()
        for r in rows:
            if r["filepath"] and os.path.exists(r["filepath"]):
                try:
                    os.remove(r["filepath"])
                except Exception:
                    pass
        cursor.execute("DELETE FROM videos WHERE status = ?", (status,))
        deleted_count = len(rows)
    elif video_ids:
        for vid_id in video_ids:
            row = cursor.execute("SELECT filepath FROM videos WHERE id = ?", (vid_id,)).fetchone()
            if row and row["filepath"] and os.path.exists(row["filepath"]):
                try:
                    os.remove(row["filepath"])
                except Exception:
                    pass
        placeholders = ",".join("?" * len(video_ids))
        cursor.execute(f"DELETE FROM videos WHERE id IN ({placeholders})", tuple(video_ids))
        deleted_count = len(video_ids)
        
    conn.commit()
    conn.close()
    return deleted_count

def get_next_pending_video():
    conn = get_db()
    row = conn.execute("SELECT * FROM videos WHERE status = 'pending' ORDER BY id ASC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None
