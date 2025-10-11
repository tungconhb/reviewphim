from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, re, os, threading
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
    # Nếu chạy localhost -> luôn cho phép
    if request.remote_addr in ['127.0.0.1', '::1']:
        return True
    
    # Nếu ở production (Render, v.v.) thì yêu cầu key
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
# ==================================================

# =================== ROUTES =======================
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

@app.route('/admin/new')
def admin_new_review():
    deny = require_admin_access()
    if deny: return deny
    return render_template('admin/new_review.html')

@app.route('/admin/add', methods=['POST'])
def admin_add_review():
    deny = require_admin_access()
    if deny: return deny
    
    title = request.form['title']
    movie_title = request.form['movie_title']
    reviewer_name = request.form['reviewer_name']
    video_url = request.form['video_url']
    description = request.form['description']
    rating = int(request.form['rating'])
    movie_link = request.form.get('movie_link', '')

    parser = YouTubeURLParser()
    video_info = parser.get_video_info(video_url)
    if not video_info:
        flash('URL video không hợp lệ!', 'error')
        return redirect(url_for('admin_new_review'))

    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''INSERT INTO video_reviews 
                (title, movie_title, reviewer_name, video_url, video_type, video_id, description, rating, movie_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (title, movie_title, reviewer_name, video_url,
                 video_info['type'], video_info['id'], description, rating, movie_link))
    conn.commit()
    conn.close()
    flash('✅ Thêm review thành công!', 'success')
    return redirect(url_for('admin_dashboard', key=ADMIN_KEY))

# ============ AUTO UPDATE (chạy nền) ============
@app.route('/admin/auto-update')
def admin_auto_update():
    deny = require_admin_access()
    if deny: return deny

    logs = []
    try:
        auto_update = get_auto_update(app)
        logs = auto_update.get_recent_logs(limit=10)
    except Exception as e:
        print(f"Error getting logs: {e}")
    return render_template('admin/auto_update.html', logs=logs)

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

# ============ AUTO-UPDATE BACKGROUND ============
@app.before_first_request
def start_auto_update():
    try:
        print("🚀 Initializing Auto-Update System...")
        auto_update = get_auto_update(app)
        print("✅ Auto-Update System ready and running in background!")
    except Exception as e:
        print(f"⚠️ Lỗi khởi động Auto-Update: {e}")
# ================================================

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
