from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import re
from datetime import datetime
import os

# ==== AI PHÂN LOẠI PHIM THÔNG MINH ====
from sentence_transformers import SentenceTransformer, util

print("🔹Đang tải mô hình AI phân loại phim...")
model = SentenceTransformer("all-MiniLM-L6-v2")
GENRES = [
    "Hành động", "Kinh dị", "Tình cảm", "Hài hước",
    "Hoạt hình", "Viễn tưởng", "Tâm lý", "Tài liệu", "Khác"
]

def analyze_movie_info(title, description, tags):
    """Phân loại phim thông minh bằng mô hình ngôn ngữ"""
    try:
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


from urllib.parse import urlparse, parse_qs

# Auto-update system imports
from services.auto_update_fixed import get_auto_update
from services.youtube_url_parser import YouTubeURLParser

app = Flask(__name__)
app.secret_key = 'reviewchill_secret_key_2025'

# Hàm phân tích tự động phim
def analyze_movie_info(title, movie_title):
    """Phân tích thông tin phim từ tiêu đề để tự động phân loại"""
    title_lower = title.lower()
    movie_title_lower = movie_title.lower()
    combined_text = f"{title_lower} {movie_title_lower}"
    
    # Phân tích quốc gia - Improved
    country = "Unknown"
    if any(keyword in combined_text for keyword in ['deadpool', 'avatar', 'spider-man', 'spiderman', 'marvel', 'dc', 'disney', 'hollywood', 'america', 'american']):
        country = "Mỹ"
    elif any(keyword in combined_text for keyword in ['trung quốc', 'china', 'hongkong', 'hong kong', 'chinese']):
        country = "Trung Quốc"
    elif any(keyword in combined_text for keyword in ['hàn quốc', 'korea', 'korean', 'k-drama', 'kdrama']):
        country = "Hàn Quốc"
    elif any(keyword in combined_text for keyword in ['nhật bản', 'japan', 'japanese', 'anime', 'manga']):
        country = "Nhật Bản"
    elif any(keyword in combined_text for keyword in ['việt nam', 'vietnam', 'vietnamese', 'việt']):
        country = "Việt Nam"
    elif any(keyword in combined_text for keyword in ['thái lan', 'thailand', 'thai']):
        country = "Thái Lan"
    
    # Phân tích thể loại - Improved with better priority
    genre = "Unknown"
    if any(keyword in combined_text for keyword in ['khoa học viễn tưởng', 'sci-fi', 'science fiction', 'siêu anh hùng', 'marvel', 'avengers', 'spider-man', 'spiderman', 'superman', 'batman']):
        genre = "Khoa học viễn tưởng"
    elif any(keyword in combined_text for keyword in ['anime', 'hoạt hình', 'animation', 'cartoon']):
        genre = "Hoạt hình"
    elif any(keyword in combined_text for keyword in ['hành động', 'action', 'fast', 'furious', 'fight', 'chiến đấu']):
        genre = "Hành động"
    elif any(keyword in combined_text for keyword in ['kinh dị', 'horror', 'ma', 'quỷ', 'zombie', 'sợ hãi']):
        genre = "Kinh dị"
    elif any(keyword in combined_text for keyword in ['tình cảm', 'romantic', 'romance', 'love', 'yêu', 'lãng mạn']):
        genre = "Tình cảm"
    elif any(keyword in combined_text for keyword in ['hài', 'comedy', 'funny', 'vui nhộn']):
        genre = "Hài"
    
    # Phân tích loại phim (single hay series)
    movie_type = "single"
    series_name = None
    episode_number = None
    
    # Tìm kiếm pattern cho phim bộ
    import re
    
    # Pattern cho tập phim
    episode_patterns = [
        r'tập\s*(\d+)', r'episode\s*(\d+)', r'ep\s*(\d+)',
        r'phần\s*(\d+)', r'season\s*(\d+)', r'part\s*(\d+)'
    ]
    
    for pattern in episode_patterns:
        match = re.search(pattern, combined_text)
        if match:
            movie_type = "series"
            episode_number = int(match.group(1))
            # Lấy tên bộ phim (loại bỏ phần tập)
            series_name = re.sub(pattern, '', movie_title, flags=re.IGNORECASE).strip()
            break
    
    # Các từ khóa cho phim bộ
    series_keywords = ['phần', 'season', 'series', 'bộ', 'saga']
    if any(keyword in combined_text for keyword in series_keywords) and movie_type == "single":
        movie_type = "series"
        series_name = movie_title
    
    return {
        'country': country,
        'genre': genre,
        'movie_type': movie_type,
        'series_name': series_name,
        'episode_number': episode_number
    }

# Khởi tạo database
def init_db():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    
    # Tạo bảng video reviews với URL video và thông tin phân loại
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
    
    # Thêm các cột mới nếu chưa có (migration)
    try:
        c.execute('ALTER TABLE video_reviews ADD COLUMN country TEXT DEFAULT "Unknown"')
    except:
        pass
    try:
        c.execute('ALTER TABLE video_reviews ADD COLUMN genre TEXT DEFAULT "Unknown"')
    except:
        pass
    try:
        c.execute('ALTER TABLE video_reviews ADD COLUMN series_name TEXT')
    except:
        pass
    try:
        c.execute('ALTER TABLE video_reviews ADD COLUMN episode_number INTEGER')
    except:
        pass
    try:
        c.execute('ALTER TABLE video_reviews ADD COLUMN movie_type TEXT DEFAULT "single"')
    except:
        pass
    
    # Cập nhật phân loại tự động cho các video hiện có
    c.execute('SELECT id, title, movie_title FROM video_reviews WHERE country = "Unknown" OR country IS NULL')
    existing_videos = c.fetchall()
    
    for video in existing_videos:
        video_id, title, movie_title = video
        analysis = analyze_movie_info(title, movie_title)
        c.execute('''UPDATE video_reviews 
                    SET country=?, genre=?, movie_type=?, series_name=?, episode_number=?
                    WHERE id=?''',
                    (analysis['country'], analysis['genre'], analysis['movie_type'], 
                     analysis['series_name'], analysis['episode_number'], video_id))
           
    conn.commit()
    conn.close()

# Hàm trích xuất video ID từ URL
def extract_video_info(url):
    """Trích xuất thông tin video từ URL YouTube hoặc Facebook"""
    if 'youtube.com/watch' in url or 'youtu.be/' in url:
        # YouTube URL
        if 'youtu.be/' in url:
            video_id = url.split('/')[-1].split('?')[0]
        else:
            parsed_url = urlparse(url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
        
        if video_id:
            return {
                'type': 'youtube',
                'id': video_id,
                'embed_url': f'https://www.youtube.com/embed/{video_id}'
            }
    
    elif 'facebook.com' in url:
        # Facebook Video URL
        # Có thể cần xử lý phức tạp hơn cho Facebook
        return {
            'type': 'facebook',
            'id': url.split('/')[-1],
            'embed_url': f'https://www.facebook.com/plugins/video.php?href={url}'
        }
    
    return None

@app.route('/')
def index():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''SELECT * FROM video_reviews ORDER BY created_at DESC''')
    reviews = c.fetchall()
    conn.close()
    
    return render_template('index.html', reviews=reviews)

@app.route('/review/<int:review_id>')
def review_detail(review_id):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews WHERE id = ?', (review_id,))
    review = c.fetchone()
    conn.close()
    
    if not review:
        flash('Không tìm thấy review!', 'error')
        return redirect(url_for('index'))
    
    # Tạo embed URL
    video_info = extract_video_info(review[4])  # video_url
    embed_url = video_info['embed_url'] if video_info else None
    
    return render_template('review_detail.html', review=review, embed_url=embed_url)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    country = request.args.get('country', '')
    genre = request.args.get('genre', '')
    
    if not query and not country and not genre:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    
    # Xây dựng câu truy vấn động
    where_conditions = []
    params = []
    
    if query:
        where_conditions.append('(title LIKE ? OR movie_title LIKE ? OR reviewer_name LIKE ?)')
        params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
    
    if country and country != 'all':
        where_conditions.append('country = ?')
        params.append(country)
    
    if genre and genre != 'all':
        where_conditions.append('genre = ?')
        params.append(genre)
    
    where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
    
    c.execute(f'''SELECT * FROM video_reviews 
                WHERE {where_clause}
                ORDER BY created_at DESC''', params)
    reviews = c.fetchall()
    
    # Lấy danh sách quốc gia và thể loại để hiển thị filter
    c.execute('SELECT DISTINCT country FROM video_reviews WHERE country IS NOT NULL ORDER BY country')
    countries = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT DISTINCT genre FROM video_reviews WHERE genre IS NOT NULL ORDER BY genre')
    genres = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return render_template('search.html', reviews=reviews, query=query, 
                         countries=countries, genres=genres, 
                         selected_country=country, selected_genre=genre)

@app.route('/filter')
def filter_movies():
    """Route để lọc phim theo quốc gia, thể loại"""
    country = request.args.get('country', 'all')
    genre = request.args.get('genre', 'all')
    movie_type = request.args.get('type', 'all')
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    
    # Xây dựng câu truy vấn
    where_conditions = ['1=1']
    params = []
    
    if country != 'all':
        where_conditions.append('country = ?')
        params.append(country)
    
    if genre != 'all':
        where_conditions.append('genre = ?')
        params.append(genre)
    
    if movie_type != 'all':
        where_conditions.append('movie_type = ?')
        params.append(movie_type)
    
    where_clause = ' AND '.join(where_conditions)
    
    c.execute(f'''SELECT * FROM video_reviews 
                WHERE {where_clause}
                ORDER BY rating DESC, created_at DESC''', params)
    reviews = c.fetchall()
    
    # Lấy thống kê
    c.execute('SELECT DISTINCT country FROM video_reviews WHERE country IS NOT NULL ORDER BY country')
    countries = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT DISTINCT genre FROM video_reviews WHERE genre IS NOT NULL ORDER BY genre')
    genres = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return render_template('filter.html', reviews=reviews, 
                         countries=countries, genres=genres,
                         selected_country=country, selected_genre=genre, selected_type=movie_type)

@app.route('/series/<series_name>')
def series_detail(series_name):
    """Hiển thị tất cả tập của một bộ phim"""
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''SELECT * FROM video_reviews 
                WHERE series_name = ? 
                ORDER BY episode_number ASC, created_at ASC''', (series_name,))
    episodes = c.fetchall()
    conn.close()
    
    if not episodes:
        flash(f'Không tìm thấy bộ phim "{series_name}"!', 'error')
        return redirect(url_for('index'))
    
    return render_template('series_detail.html', episodes=episodes, series_name=series_name)

# Helper function để kiểm tra localhost
def is_localhost():
    """Kiểm tra xem request có phải từ localhost không"""
    remote_addr = request.environ.get('REMOTE_ADDR', '')
    http_host = request.environ.get('HTTP_HOST', '')
    
    localhost_ips = ['127.0.0.1', '::1']
    localhost_hosts = ['localhost', '127.0.0.1']
    
    # Kiểm tra IP
    if remote_addr in localhost_ips:
        return True
    
    # Kiểm tra host
    if any(host in http_host for host in localhost_hosts):
        return True
    
    return False

# Admin routes (chỉ cho phép truy cập từ localhost)
@app.route('/admin')
def admin_dashboard():
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    
    return render_template('admin/dashboard.html', reviews=reviews)

@app.route('/admin/new')
def admin_new_review():
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    return render_template('admin/new_review.html')

@app.route('/admin/add', methods=['POST'])
def admin_add_review():
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    title = request.form['title']
    movie_title = request.form['movie_title']
    reviewer_name = request.form['reviewer_name']
    video_url = request.form['video_url']
    description = request.form['description']
    rating = int(request.form['rating'])
    movie_link = request.form.get('movie_link', '')
    
    # Trích xuất thông tin video
    video_info = extract_video_info(video_url)
    if not video_info:
        flash('URL video không hợp lệ! Hỗ trợ YouTube và Facebook.', 'error')
        return redirect(url_for('admin_new_review'))
    
    # Tự động phân tích thông tin phim
    analysis = analyze_movie_info(title, movie_title)
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''INSERT INTO video_reviews 
                (title, movie_title, reviewer_name, video_url, video_type, video_id, description, rating, movie_link, country, genre, series_name, episode_number, movie_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (title, movie_title, reviewer_name, video_url, video_info['type'], 
                 video_info['id'], description, rating, movie_link,
                 analysis['country'], analysis['genre'], analysis['series_name'], 
                 analysis['episode_number'], analysis['movie_type']))
    conn.commit()
    conn.close()
    
    flash(f'Thêm video review thành công! Phân loại: {analysis["country"]} - {analysis["genre"]}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:review_id>')
def admin_edit_review(review_id):
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews WHERE id = ?', (review_id,))
    review = c.fetchone()
    conn.close()
    
    if not review:
        flash('Không tìm thấy review!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_review.html', review=review)

@app.route('/admin/update/<int:review_id>', methods=['POST'])
def admin_update_review(review_id):
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    title = request.form['title']
    movie_title = request.form['movie_title']
    reviewer_name = request.form['reviewer_name']
    video_url = request.form['video_url']
    description = request.form['description']
    rating = int(request.form['rating'])
    movie_link = request.form['movie_link']
    
    # Trích xuất thông tin video
    video_info = extract_video_info(video_url)
    if not video_info:
        flash('URL video không hợp lệ! Hỗ trợ YouTube và Facebook.', 'error')
        return redirect(url_for('admin_edit_review', review_id=review_id))
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('''UPDATE video_reviews 
                SET title=?, movie_title=?, reviewer_name=?, video_url=?, video_type=?, video_id=?, 
                    description=?, rating=?, movie_link=?
                WHERE id=?''',
                (title, movie_title, reviewer_name, video_url, video_info['type'], 
                 video_info['id'], description, rating, movie_link, review_id))
    conn.commit()
    conn.close()
    
    flash('Cập nhật video review thành công!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:review_id>')
def admin_delete_review(review_id):
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('DELETE FROM video_reviews WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    
    flash('Xóa video review thành công!', 'success')
    return redirect(url_for('admin_dashboard'))

# Auto-update system routes
@app.route('/admin/auto-update')
def admin_auto_update():
    if not is_localhost():
        flash('Tính năng quản trị chỉ khả dụng khi truy cập từ localhost!', 'error')
        return redirect(url_for('index'))
    
    # Get logs from auto-update system
    logs = []
    try:
        auto_update = get_auto_update(app)
        logs = auto_update.get_recent_logs(limit=10)
    except Exception as e:
        print(f"Error getting logs: {e}")
    
    return render_template('admin/auto_update.html', logs=logs)

@app.route('/admin/auto-update/stats')
def admin_auto_update_stats():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        auto_update = get_auto_update(app)
        
        # Get total videos count
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM video_reviews')
        total_videos = c.fetchone()[0]
        conn.close()
        
        # Get auto-update stats
        stats = auto_update.get_stats()
        stats['total_videos_added'] = total_videos
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error getting auto-update stats: {e}")
        return jsonify({
            'enabled': False,
            'total_videos_added': 0,
            'last_successful_update': None,
            'error': str(e)
        })

@app.route('/admin/auto-update/toggle', methods=['POST'])
def admin_auto_update_toggle():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        auto_update = get_auto_update(app)
        
        if enabled:
            auto_update.enable()
            message = 'Hệ thống tự động cập nhật đã được kích hoạt'
        else:
            auto_update.disable()
            message = 'Hệ thống tự động cập nhật đã được tạm dừng'
        
        return jsonify({
            'success': True,
            'message': message,
            'enabled': enabled
        })
    except Exception as e:
        print(f"Error toggling auto-update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin/auto-update/run', methods=['POST'])
def admin_auto_update_run():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        auto_update = get_auto_update(app)
        result = auto_update.run_update()
        
        return jsonify({
            'success': True,
            'message': f'Cập nhật thành công! Tìm thấy {result.get("found", 0)} video, thêm mới {result.get("added", 0)} video',
            'result': result
        })
    except Exception as e:
        print(f"Error running manual update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin/auto-update/videos')
def admin_auto_update_videos():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        c.execute('''SELECT id, title, movie_title, reviewer_name, created_at 
                    FROM video_reviews ORDER BY created_at DESC''')
        videos = c.fetchall()
        conn.close()
        
        video_list = []
        for video in videos:
            video_list.append({
                'id': video[0],
                'title': video[1],
                'movie_title': video[2],
                'channel': video[3],  # reviewer_name as channel
                'created_at': video[4]
            })
        
        return jsonify({
            'success': True,
            'videos': video_list,
            'total': len(video_list)
        })
    except Exception as e:
        print(f"Error getting videos list: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'videos': [],
            'total': 0
        })

@app.route('/admin/auto-update/run-manual', methods=['POST'])
def admin_auto_update_run_manual():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        auto_update = get_auto_update(app)
        result = auto_update.run_update()
        
        return jsonify({
            'success': True,
            'message': f'Cập nhật thành công! Tìm thấy {result.get("found", 0)} video, thêm mới {result.get("added", 0)} video',
            'result': result
        })
    except Exception as e:
        print(f"Error running manual update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin/auto-update/get-videos')
def admin_auto_update_get_videos():
    """Alias for videos endpoint to match JavaScript calls"""
    return admin_auto_update_videos()

@app.route('/admin/auto-update/logs')
def admin_auto_update_logs():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        c.execute('''SELECT timestamp, status, message, videos_found, videos_added 
                    FROM update_logs ORDER BY timestamp DESC LIMIT 20''')
        logs = c.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        print(f"Error getting logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': []
        })

@app.route('/admin/auto-update/bulk-operations', methods=['POST'])
def admin_auto_update_bulk_operations():
    if not is_localhost():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        operation = data.get('operation')
        
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        
        if operation == 'delete_selected':
            video_ids = data.get('video_ids', [])
            if not video_ids:
                return jsonify({'success': False, 'error': 'Không có video nào được chọn'})
            
            # Delete selected videos
            placeholders = ','.join(['?' for _ in video_ids])
            c.execute(f'DELETE FROM video_reviews WHERE id IN ({placeholders})', video_ids)
            
            deleted_count = c.rowcount
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Đã xóa {deleted_count} video thành công'
            })
            
        elif operation == 'delete_all':
            # Delete all videos
            c.execute('DELETE FROM video_reviews')
            deleted_count = c.rowcount
            
            # Reset auto-increment counter
            c.execute("DELETE FROM sqlite_sequence WHERE name='video_reviews'")
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Đã xóa tất cả {deleted_count} video và reset ID thành công'
            })
            
        elif operation == 'reset_ids':
            # Get all videos ordered by creation date
            c.execute('SELECT * FROM video_reviews ORDER BY created_at ASC')
            videos = c.fetchall()
            
            if not videos:
                conn.close()
                return jsonify({
                    'success': True,
                    'message': 'Không có video nào để reset ID'
                })
            
            # Delete all videos
            c.execute('DELETE FROM video_reviews')
            
            # Reset auto-increment counter
            c.execute("DELETE FROM sqlite_sequence WHERE name='video_reviews'")
            
            # Re-insert videos with new sequential IDs (skip ID column)
            for video in videos:
                c.execute('''INSERT INTO video_reviews 
                            (title, movie_title, reviewer_name, video_url, video_type, video_id, 
                             description, rating, movie_link, created_at, channel_name, 
                             thumbnail_url, published_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            video[1:])  # Skip the old ID (video[0])
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Đã reset ID cho {len(videos)} video thành công'
            })
            
        else:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Thao tác không hợp lệ: {operation}'
            })
            
    except Exception as e:
        print(f"Error in bulk operations: {e}")
        return jsonify({
            'success': False,
            'error': f'Lỗi xử lý: {str(e)}'
        })

# API endpoints
@app.route('/api/reviews')
def api_reviews():
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute('SELECT * FROM video_reviews ORDER BY created_at DESC')
    reviews = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': r[0],
        'title': r[1],
        'movie_title': r[2],
        'reviewer_name': r[3],
        'video_url': r[4],
        'video_type': r[5],
        'video_id': r[6],
        'description': r[7],
        'rating': r[8],
        'movie_link': r[9],
        'created_at': r[10]
    } for r in reviews])

@app.route('/admin/preview-youtube', methods=['POST'])
def preview_youtube():
    """Preview YouTube video info before adding"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL không được để trống'})
        
        parser = YouTubeURLParser()
        video_info = parser.get_video_info(url)
        
        if video_info:
            return jsonify({
                'success': True,
                'video_info': video_info
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Không thể lấy thông tin video. Kiểm tra lại URL.'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'})

@app.route('/admin/add-manual-video', methods=['POST'])
def add_manual_video():
    """Add YouTube video manually"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        custom_title = data.get('custom_title', '').strip()
        custom_description = data.get('custom_description', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL không được để trống'})
        
        parser = YouTubeURLParser()
        video_info = parser.get_video_info(url)
        
        if not video_info:
            return jsonify({
                'success': False, 
                'error': 'Không thể lấy thông tin video. Kiểm tra lại URL.'
            })
        
        # Add to database
        result = parser.add_video_to_database(
            video_info, 
            custom_title=custom_title or None,
            custom_description=custom_description or None
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'})

@app.route('/admin/check-api-status')
def check_api_status():
    """Check YouTube API status"""
    try:
        from services.smart_youtube_service import SmartYouTubeService
        service = SmartYouTubeService()
        
        # Check if we have real API key
        api_key = service.get_current_api_key()
        if not api_key or api_key == 'DEMO_KEY_SMART_MODE':
            return jsonify({
                'success': True,
                'status': 'demo',
                'message': 'Demo mode - cần YouTube API key'
            })
        
        # Try a simple API call
        try:
            videos = service.search_youtube_api('test', max_results=1)
            if videos:
                return jsonify({
                    'success': True,
                    'status': 'connected',
                    'message': 'API đã kết nối'
                })
            else:
                return jsonify({
                    'success': True,
                    'status': 'error',
                    'message': 'API key không hoạt động'
                })
        except Exception as api_error:
            return jsonify({
                'success': True,
                'status': 'error',
                'message': f'Lỗi API: {str(api_error)}'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi kiểm tra: {str(e)}'})

@app.route('/api/get_related_videos/<int:current_video_id>')
def get_related_videos(current_video_id):
    """API để lấy video đề xuất liên quan với ưu tiên phim cùng bộ"""
    try:
        conn = sqlite3.connect('db.sqlite')
        c = conn.cursor()
        
        # Lấy thông tin video hiện tại
        c.execute('''SELECT movie_title, reviewer_name, series_name, movie_type, country, genre 
                     FROM video_reviews WHERE id = ?''', (current_video_id,))
        current_video = c.fetchone()
        
        if not current_video:
            return jsonify({'success': False, 'error': 'Video không tồn tại'})
        
        current_movie, current_reviewer, current_series, current_type, current_country, current_genre = current_video
        
        related_videos = []
        
        # Ưu tiên 1: Video cùng bộ phim (nếu là phim bộ)
        if current_type == 'series' and current_series:
            c.execute('''
                SELECT id, title, movie_title, reviewer_name, video_id, video_type, rating, country, genre, series_name, episode_number
                FROM video_reviews 
                WHERE id != ? AND series_name = ? AND movie_type = 'series'
                ORDER BY episode_number ASC, rating DESC
                LIMIT 2
            ''', (current_video_id, current_series))
            series_videos = c.fetchall()
            related_videos.extend(series_videos)
        
        # Ưu tiên 2: Video cùng reviewer và cùng thể loại
        if len(related_videos) < 3:
            c.execute('''
                SELECT id, title, movie_title, reviewer_name, video_id, video_type, rating, country, genre, series_name, episode_number
                FROM video_reviews 
                WHERE id != ? AND reviewer_name = ? AND genre = ? 
                AND (series_name != ? OR series_name IS NULL)
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            ''', (current_video_id, current_reviewer, current_genre, current_series, 3 - len(related_videos)))
            reviewer_videos = c.fetchall()
            related_videos.extend(reviewer_videos)
        
        # Ưu tiên 3: Video cùng quốc gia và thể loại
        if len(related_videos) < 3:
            c.execute('''
                SELECT id, title, movie_title, reviewer_name, video_id, video_type, rating, country, genre, series_name, episode_number
                FROM video_reviews 
                WHERE id != ? AND country = ? AND genre = ?
                AND reviewer_name != ?
                AND (series_name != ? OR series_name IS NULL)
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            ''', (current_video_id, current_country, current_genre, current_reviewer, current_series, 3 - len(related_videos)))
            country_videos = c.fetchall()
            related_videos.extend(country_videos)
        
        # Ưu tiên 4: Video cùng thể loại (nếu vẫn chưa đủ)
        if len(related_videos) < 3:
            c.execute('''
                SELECT id, title, movie_title, reviewer_name, video_id, video_type, rating, country, genre, series_name, episode_number
                FROM video_reviews 
                WHERE id != ? AND genre = ?
                AND reviewer_name != ? AND country != ?
                AND (series_name != ? OR series_name IS NULL)
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            ''', (current_video_id, current_genre, current_reviewer, current_country, current_series, 3 - len(related_videos)))
            genre_videos = c.fetchall()
            related_videos.extend(genre_videos)
        
        # Ưu tiên 5: Video ngẫu nhiên (nếu vẫn chưa đủ)
        if len(related_videos) < 3:
            c.execute('''
                SELECT id, title, movie_title, reviewer_name, video_id, video_type, rating, country, genre, series_name, episode_number
                FROM video_reviews 
                WHERE id != ? 
                AND (series_name != ? OR series_name IS NULL)
                ORDER BY rating DESC, created_at DESC
                LIMIT ?
            ''', (current_video_id, current_series, 3 - len(related_videos)))
            random_videos = c.fetchall()
            related_videos.extend(random_videos)
        
        conn.close()
        
        # Loại bỏ trùng lặp và format dữ liệu trả về
        seen_ids = set()
        unique_videos = []
        for video in related_videos:
            if video[0] not in seen_ids:
                seen_ids.add(video[0])
                unique_videos.append(video)
                if len(unique_videos) >= 3:
                    break
        
        videos = []
        for video in unique_videos:
            video_data = {
                'id': video[0],
                'title': video[1],
                'movie_title': video[2],
                'reviewer_name': video[3],
                'video_id': video[4],
                'video_type': video[5],
                'rating': video[6],
                'country': video[7] if len(video) > 7 else 'Unknown',
                'genre': video[8] if len(video) > 8 else 'Unknown',
                'series_name': video[9] if len(video) > 9 else None,
                'episode_number': video[10] if len(video) > 10 else None,
                'thumbnail_url': f'https://img.youtube.com/vi/{video[4]}/hqdefault.jpg' if video[5] == 'youtube' else None
            }
            videos.append(video_data)
        
        return jsonify({
            'success': True,
            'videos': videos,
            'current_info': {
                'series': current_series,
                'type': current_type,
                'country': current_country,
                'genre': current_genre
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'})

if __name__ == '__main__':
    init_db()
    
    # Initialize auto-update system
    print("🚀 Initializing Auto-Update System...")
    auto_update = get_auto_update(app)
    print("✅ Auto-Update System ready!")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
