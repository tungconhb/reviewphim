"""
Smart Update Videos - Cập nhật toàn bộ video trong DB với phân loại AI
"""

import sqlite3
from sentence_transformers import SentenceTransformer, util
from datetime import datetime

# -------------------- Cấu hình mô hình AI --------------------
model = SentenceTransformer('paraphrase-MiniLM-L3-v2')

AI_GENRES = [
    'Hành động', 'Kinh dị', 'Viễn tưởng', 'Tình cảm', 'Hài hước',
    'Chính kịch', 'Hoạt hình', 'Phiêu lưu', 'Tâm lý', 'Thần thoại'
]

def analyze_movie_info(title, description, tags=None):
    """Phân loại phim thông minh bằng mô hình ngôn ngữ"""
    try:
        tags = tags or []
        text = f"{title} {description or ''} {' '.join(tags)}"
        emb_text = model.encode(text, convert_to_tensor=True)
        emb_genres = model.encode(AI_GENRES, convert_to_tensor=True)
        scores = util.cos_sim(emb_text, emb_genres)
        best_genre = AI_GENRES[int(scores.argmax())]
        return {
            'genre': best_genre,
            'country': 'Unknown',
            'movie_type': 'Unknown',
            'series_name': '',
            'episode_number': 0
        }
    except Exception as e:
        print("⚠️ Lỗi AI phân loại:", e)
        return {
            'genre': 'Unknown',
            'country': 'Unknown',
            'movie_type': 'Unknown',
            'series_name': '',
            'episode_number': 0
        }

# -------------------- Cập nhật DB --------------------
def update_all_videos_in_db():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()

    # Kiểm tra xem cột cần thiết có tồn tại không
    cursor.execute("PRAGMA table_info(video_reviews)")
    columns = [row[1] for row in cursor.fetchall()]
    required_columns = ['title', 'description', 'genre', 'country', 'movie_type']
    for col in required_columns:
        if col not in columns:
            raise Exception(f"Cột '{col}' chưa tồn tại trong bảng video_reviews. Cần tạo trước.")

    # Lấy tất cả video
    cursor.execute("SELECT id, title, description FROM video_reviews")
    videos = cursor.fetchall()
    updated_count = 0

    print("🔄 Updating all videos in DB with AI classification...")

    for video in videos:
        video_id, title, description = video
        analysis = analyze_movie_info(title, description)
        try:
            cursor.execute('''
                UPDATE video_reviews
                SET genre = ?, country = ?, movie_type = ?, series_name = ?, episode_number = ?
                WHERE id = ?
            ''', (
                analysis['genre'],
                analysis['country'],
                analysis['movie_type'],
                analysis['series_name'],
                analysis['episode_number'],
                video_id
            ))
            updated_count += 1
            print(f"✅ Updated: {title[:50]}... -> {analysis['genre']}")
        except Exception as e:
            print(f"❌ Error updating video {video_id}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Completed! Total videos updated: {updated_count}")

# -------------------- Chạy script --------------------
if __name__ == "__main__":
    update_all_videos_in_db()
