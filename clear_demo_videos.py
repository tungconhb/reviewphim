import sqlite3

# Kết nối DB
conn = sqlite3.connect("db.sqlite")
cursor = conn.cursor()

# Xóa video demo (video_url bắt đầu bằng VN là video fake demo)
cursor.execute("DELETE FROM video_reviews WHERE video_url LIKE 'https://www.youtube.com/watch?v=VN%'")

conn.commit()
conn.close()

print("✅ Đã xóa tất cả video demo cũ.")
