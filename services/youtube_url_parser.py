"""
YouTube URL Parser - Lấy thông tin video từ YouTube URL
Hoạt động mà không cần API key
"""

import re
import requests
import json
from datetime import datetime
import sqlite3

class YouTubeURLParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*?v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, url):
        """Get video information from YouTube URL"""
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                return None
            
            # Try multiple methods to get video info
            video_info = self.get_info_from_embed(video_id)
            if not video_info:
                video_info = self.get_info_from_oembed(video_id)
            
            if video_info:
                video_info['video_id'] = video_id
                video_info['video_url'] = f"https://www.youtube.com/watch?v={video_id}"
                video_info['thumbnail'] = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                
            return video_info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_info_from_oembed(self, video_id):
        """Get info using YouTube oEmbed API (no key required)"""
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', 'YouTube Video'),
                    'channel': data.get('author_name', 'Unknown Channel'),
                    'description': f"Video từ kênh {data.get('author_name', 'Unknown')}",
                    'thumbnail_width': data.get('thumbnail_width'),
                    'thumbnail_height': data.get('thumbnail_height')
                }
        except Exception as e:
            print(f"oEmbed error: {e}")
        return None
    
    def get_info_from_embed(self, video_id):
        """Get info from YouTube embed page"""
        try:
            url = f"https://www.youtube.com/embed/{video_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Extract title from page title
                title_match = re.search(r'<title>(.*?)</title>', html)
                title = title_match.group(1) if title_match else f"YouTube Video {video_id}"
                
                # Clean title
                title = title.replace(' - YouTube', '').strip()
                
                return {
                    'title': title,
                    'channel': 'YouTube Channel',
                    'description': f"Video từ YouTube với ID: {video_id}"
                }
        except Exception as e:
            print(f"Embed error: {e}")
        return None
    
    def add_video_to_database(self, video_info, custom_title=None, custom_description=None):
        """Add video to database"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            
            # Check if video already exists
            cursor.execute(
                'SELECT id FROM video_reviews WHERE video_url = ?',
                (video_info['video_url'],)
            )
            
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'error': 'Video đã tồn tại trong database'}
            
            # Use custom title/description if provided
            title = custom_title if custom_title else video_info['title']
            description = custom_description if custom_description else video_info['description']
            
            # Insert video
            cursor.execute('''
                INSERT INTO video_reviews 
                (title, movie_title, reviewer_name, video_url, video_type, video_id, 
                 description, rating, movie_link, channel_name, thumbnail_url, 
                 published_at, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                title,  # movie_title = title
                video_info['channel'],  # reviewer_name
                video_info['video_url'],
                'youtube',  # video_type
                video_info['video_id'],
                description,
                7,  # Default rating
                '',  # movie_link
                video_info['channel'],  # channel_name
                video_info['thumbnail'],  # thumbnail_url
                datetime.now().isoformat(),  # published_at
                datetime.now().isoformat(),  # updated_at
                datetime.now().isoformat()   # created_at
            ))
            
            conn.commit()
            video_id = cursor.lastrowid
            conn.close()
            
            return {
                'success': True, 
                'message': 'Video đã được thêm thành công!',
                'video_id': video_id,
                'title': title
            }
            
        except Exception as e:
            print(f"Database error: {e}")
            return {'success': False, 'error': f'Lỗi database: {str(e)}'}

def test_parser():
    """Test function"""
    parser = YouTubeURLParser()
    
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ"
    ]
    
    for url in test_urls:
        print(f"\n🧪 Testing: {url}")
        info = parser.get_video_info(url)
        if info:
            print(f"✅ Title: {info['title']}")
            print(f"✅ Channel: {info['channel']}")
            print(f"✅ Video ID: {info['video_id']}")
        else:
            print("❌ Failed to get info")

if __name__ == "__main__":
    test_parser()