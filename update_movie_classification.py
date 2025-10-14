import sqlite3
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
GENRES = ['Hành động', 'Kinh dị', 'Viễn tưởng', 'Tình cảm', 'Hài hước', 
          'Chính kịch', 'Hoạt hình', 'Phiêu lưu', 'Tâm lý', 'Thần thoại']

def analyze_genre(title, description):
    text = f"{title} {description or ''}"
    emb_text = model.encode(text, convert_to_tensor=True)
    emb_genres = model.encode(GENRES, convert_to_tensor=True)
    scores = util.cos_sim(emb_text, emb_genres)
    return GENRES[int(scores.argmax())]

conn = sqlite3.connect('db.sqlite')
c = conn.cursor()
c.execute("SELECT id, title, description FROM video_reviews")
videos = c.fetchall()

for vid in videos:
    vid_id, title, desc = vid
    genre = analyze_genre(title, desc)
    c.execute("UPDATE video_reviews SET genre = ? WHERE id = ?", (genre, vid_id))

conn.commit()
conn.close()
print("✅ Đã cập nhật toàn bộ video theo AI")

# --- Compatibility shim ---
def analyze_movie_info(*args, **kwargs):
    """
    Hàm tương thích cho AI classification.
    Có thể gọi bằng:
        analyze_movie_info(title, description)
    hoặc:
        analyze_movie_info({"title": ..., "description": ...})
    """
    try:
        if len(args) == 2:
            title, desc = args
        elif len(args) == 1:
            video_info = args[0]
            if isinstance(video_info, dict):
                title = video_info.get("title", "")
                desc = video_info.get("description", "")
            elif isinstance(video_info, (list, tuple)):
                title = video_info[0]
                desc = video_info[1] if len(video_info) > 1 else ""
            else:
                title, desc = str(video_info), ""
        else:
            title, desc = "", ""

        genre = analyze_genre(title, desc)
        return {"title": title, "description": desc, "genre": genre}
    except Exception as e:
        print(f"⚠️ analyze_movie_info() error: {e}")
        return {"title": "", "description": "", "genre": "Không xác định"}

