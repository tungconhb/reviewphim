from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, os, threading, re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from sentence_transformers import SentenceTransformer, util

# ===================== CONFIG =====================
ADMIN_KEY = os.environ.get("ADMIN_KEY", "my_secret_admin_key_2025")
IS_PRODUCTION = os.environ.get("IS_PRODUCTION", "true").lower() == "true"
# ==================================================

# ==== AI PHÂN LOẠI PHIM THÔNG MINH ====
model = None
GENRES = [
    "Hành động", "Kinh dị", "Tình cảm", "Hài hước",
    "Hoạt hình", "Viễn tưởng", "Tâm lý", "Tài liệu", "Khác"
]

def preload_model():
    global model
    try:
        print("🔹Đang tải mô hình AI phân loại phim (nền)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Mô hình AI đã tải xong!")
    except Exception as e:
        print("⚠️ Lỗi tải mô hình:", e)

threading.Thread(target=preload_model).start()

def analyze_movie_info(title, description, tags):
    """Phân loại phim thông minh bằng mô hình ngôn ngữ"""
    try:
        if not model:
            return "Khác"
        text = f"{title} {description or ''} {' '.join(tags or [])}"
        emb_text = model.encode(text, convert_to_tensor=True)
        emb_genres = model.encode(GENRES, convert_to_tensor=True)
        scores = util.cos_sim(emb_text, emb_genres)
        best_genre = GENRES[int(scores.argmax())]
        return best_genre
    except Exception as e:
        print("⚠️ Lỗi AI phân loại:", e)
        return "Khác"

# =========================================
from services.auto_update_fixed import get_auto_update
from services.youtube_url_parser import YouTubeURLParser

app = Flask(__name__)
app.secret_key = 'reviewchill_secret_key_2025'

# ==================================================
# 🔐 HÀM XÁC THỰC ADMIN
# ==================================================
def is_admin_request():
    """Kiểm tra xem request có quyền admin không"""
    if request.remote_addr in ['127.0.0.1', '::1']:
        return True
    if IS_PRODUCTION:
        key = request.args.get("key") or request.headers.get("X-Admin-Key")
        if key and key == ADMIN_KEY:
            return True
        return False
    return True

def require_admin_access():
    """Tự động chặn request nếu không có quyền admin"""
    if not is_admin_request():
        flash("Truy cập bị từ chối: bạn không có quyền admin!", "error")
        return redirect(url_for("index"))
    return None
# ==================================================

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS video_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    movie_title TEXT NOT NULL,
                    reviewer_name TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    video_type TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    description TEXT,
                    rating INTEGER,
                    movie_link TEXT,
                    country TEXT DEFAULT 'Unknown',
                    genre TEXT DEFAULT 'Unknown',
                    series_name TEXT,
                    episode_number INTEGER,
                    movie_type TEXT DEFAULT 'single',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def init_stats_db():
    """Tạo bảng thống kê truy cập nếu chưa có"""
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    ip TEXT,
                    path TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()
# ==================================================

# =================== MIDDLEWARE ===================
@app.before_request
def log_access():
    """Ghi lại lượt truy cập"""
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        path = request.path
        ua = request.headers.get('User-Agent', 'Unknown')
        if path.startswith('/static') or path.startswith('/health'):
            return
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        c.execute('INSERT INTO access_logs (date, ip, path, user_agent) VALUES (?, ?, ?, ?)',
                  (today, ip, path, ua))
        conn.commit()
        conn.close()
    except Exception as e:
        print("⚠️ Lỗi ghi log truy cập:", e)
# ==================================================

@app.route("/health")
def health_check():
    return jsonify(status="ok", model_loaded=model is not None), 200

@app.route('/')
def index():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    return render_template('index.html', reviews=reviews)

# ============ ADMIN DASHBOARD =============
@app.route('/admin')
def admin_dashboard():
    deny = require_admin_access()
    if deny: return deny

    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    return render_template('admin/dashboard.html', reviews=reviews)

# ============ THỐNG KÊ TRUY CẬP ============
@app.route('/admin/stats')
def admin_stats():
    deny = require_admin_access()
    if deny: return deny
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''SELECT date, COUNT(*) as visits FROM access_logs 
                 GROUP BY date ORDER BY date DESC LIMIT 30''')
    daily_stats = c.fetchall()
    c.execute('SELECT COUNT(*), COUNT(DISTINCT ip) FROM access_logs')
    total_visits, unique_visitors = c.fetchone()
    conn.close()
    return render_template('admin/stats.html',
                           daily_stats=daily_stats,
                           total_visits=total_visits,
                           unique_visitors=unique_visitors)
# ==================================================

# ============ API ======================
@app.route('/api/reviews')
def api_reviews():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    return jsonify([
        {'id': r[0], 'title': r[1], 'movie_title': r[2], 'reviewer_name': r[3], 'video_url': r[4]} for r in reviews
    ])
# =======================================

@app.before_first_request
def start_auto_update():
    try:
        print("🚀 Initializing Auto-Update System...")
        auto_update = get_auto_update(app)
        print("✅ Auto-Update System ready and running in background!")
    except Exception as e:
        print(f"⚠️ Lỗi khởi động Auto-Update: {e}")

if __name__ == '__main__':
    init_db()
    init_stats_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
