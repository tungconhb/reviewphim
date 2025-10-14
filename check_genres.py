import sqlite3

conn = sqlite3.connect('db.sqlite')
c = conn.cursor()

c.execute("SELECT DISTINCT genre FROM video_reviews ORDER BY genre")
genres = [row[0] for row in c.fetchall()]

print("Genres in DB:", genres)

conn.close()
