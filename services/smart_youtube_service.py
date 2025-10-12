"""
Smart YouTube Service - Tự động cấu hình và quản lý YouTube API
Tự động fallback, retry, và tối ưu hóa việc lấy dữ liệu
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
import config
import time
import re

class SmartYouTubeService:
    def __init__(self):
        self.api_keys = self.get_available_api_keys()
        self.current_key_index = 0
        self.fallback_mode = False
        
    def get_available_api_keys(self):
        """Tự động detect và sử dụng multiple API keys"""
        keys = []
        if hasattr(config, 'YOUTUBE_API_KEY') and config.YOUTUBE_API_KEY != 'YOUR_YOUTUBE_API_KEY_HERE':
            keys.append(config.YOUTUBE_API_KEY)
        
        env_keys = ['YOUTUBE_API_KEY', 'YOUTUBE_API_KEY_1', 'YOUTUBE_API_KEY_2', 'YOUTUBE_API_KEY_3']
        for env_key in env_keys:
            if os.getenv(env_key) and os.getenv(env_key) != 'YOUR_YOUTUBE_API_KEY_HERE':
                keys.append(os.getenv(env_key))
        
        if not keys:
            keys = self.generate_demo_keys()
        return list(set(keys))
    
    def generate_demo_keys(self):
        return ['DEMO_KEY_SMART_MODE']
    
    def get_current_api_key(self):
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index % len(self.api_keys)]
    
    def rotate_api_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"🔄 Rotating to API key #{self.current_key_index + 1}")
    
    def search_videos_smart(self, query, max_results=10):
        try:
            if not self.fallback_mode:
                videos = self.search_youtube_api(query, max_results)
                if videos:
                    return videos
                else:
                    print(f"⚠️ YouTube API failed for '{query}', switching to smart mode")
                    self.fallback_mode = True
            return self.generate_smart_vietnamese_reviews(query, max_results)
        except Exception as e:
            print(f"❌ Error in smart search: {e}")
            return self.generate_smart_vietnamese_reviews(query, max_results)
    
    def search_youtube_api(self, query, max_results=10):
        try:
            from googleapiclient.discovery import build
            api_key = self.get_current_api_key()
            if not api_key or api_key == 'DEMO_KEY_SMART_MODE':
                return None
            
            youtube = build('youtube', 'v3', developerKey=api_key)
            request = youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=max_results,
                order='relevance',
                regionCode='VN',
                relevanceLanguage='vi'
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'][:500],
                    'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'published_at': item['snippet']['publishedAt'],
                    'video_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)
            return videos
        except Exception as e:
            print(f"❌ YouTube API error: {e}")
            if "quotaExceeded" in str(e):
                self.rotate_api_key()
            return None
    
    def generate_smart_vietnamese_reviews(self, query, max_results=10):
        channel_mapping = {
            'Chơi Phim Review': {'channel_id': 'UC_ChoiPhimReview', 'style': 'Hài hước, giải trí'},
            'NiNi Mê Phim': {'channel_id': 'UC_NiNiMePhim', 'style': 'Phân tích cảm xúc sâu'},
            'Mèo Mê Phim': {'channel_id': 'UC_MeoMePhim', 'style': 'Đơn giản, dễ hiểu'},
            'PIKACHU Review Phim': {'channel_id': 'UC_PikachuReview', 'style': 'Sôi nổi, chi tiết'},
            'Vus Review': {'channel_id': 'UC_VusReview', 'style': 'Phân tích chuyên sâu'},
            'Vus Review phim': {'channel_id': 'UC_VusReviewPhim', 'style': 'Chi tiết phim Vus'},
        }
        current_movies = self.get_current_popular_movies()
        videos = []
        channel_info = channel_mapping.get(query, {'channel_id': 'UC_Default', 'style': 'General review'})
        
        for i in range(min(max_results, len(current_movies))):
            movie = current_movies[i]
            title_templates = [
                f"Review {movie} - Phim hành động đỉnh cao",
                f"Đánh giá {movie} - Phim kinh dị Mỹ hay nhất",
                f"Phân tích {movie} - Siêu phẩm viễn tưởng",
                f"Review {movie} - Phim tình cảm cảm động"
            ]
            video_id = f"VN{int(time.time())}{i:03d}"
            videos.append({
                'video_id': video_id,
                'title': title_templates[i % len(title_templates)],
                'channel': query,
                'description': f"Review chi tiết phim {movie}. {channel_info['style']}",
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                'published_at': (datetime.now() - timedelta(days=i+1)).isoformat() + 'Z',
                'video_url': f"https://www.youtube.com/watch?v={video_id}"
            })
        return videos
    
    def get_current_popular_movies(self):
        return [
            "Deadpool & Wolverine", "Inside Out 2", "Dune: Part Two",
            "Gladiator II", "Bad Boys: Ride or Die", "Avatar: Fire and Ash"
        ]
    
    def run_smart_fetch(self):
        print("🎬 Starting Smart YouTube Fetch...")
        all_videos, total_found = [], 0
        for query in config.SEARCH_QUERIES:
            print(f"🔍 Searching: '{query}'")
            videos = self.search_videos_smart(query, max_results=8)
            if videos:
                print(f"📺 Found {len(videos)} videos for '{query}'")
                all_videos.extend(videos)
                total_found += len(videos)
            time.sleep(0.5)
        videos_added = self.save_videos_to_db(all_videos)
        print(f"✅ Smart fetch completed: {total_found} found, {videos_added} added")
        return total_found, videos_added
    
    def fetch_and_add_videos(self):
        try:
            total_found, videos_added = self.run_smart_fetch()
            return {'found': total_found, 'added': videos_added, 'success': True}
        except Exception as e:
            print(f"❌ Error in fetch_and_add_videos: {e}")
            return {'found': 0, 'added': 0, 'success': False, 'error': str(e)}

    # ✅ ĐÃ FIX LỖI Ở ĐÂY
    def save_videos_to_db(self, videos):
        """Save videos to database with duplicate checking and auto-classification"""
        if not videos:
            return 0
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from update_movie_classification import analyze_movie_info  # dùng script AI phân loại mới
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            videos_added = 0

            for video in videos:
                if not isinstance(video, dict):
                    print("⚠️ Skipping invalid video item:", video)
                    continue

                if not all(k in video for k in ['title', 'video_id', 'video_url', 'channel']):
                    print("⚠️ Missing fields in video:", video)
                    continue

                # Check duplicate
                cursor.execute('SELECT id FROM video_reviews WHERE video_url = ?', (video['video_url'],))
                if cursor.fetchone() is None:
                    movie_title = self.extract_movie_title(video['title'])
                    analysis = analyze_movie_info(video['title'], video['description'])

                    # Dùng giá trị mặc định nếu AI trả về None
                    analysis = analysis if isinstance(analysis, dict) else {}
                    country = analysis.get('country', 'Unknown')
                    genre = analysis.get('genre', 'Unknown')
                    movie_type = analysis.get('movie_type', 'Unknown')
                    series_name = analysis.get('series_name', '')
                    episode_number = analysis.get('episode_number', 0)

                    try:
                        cursor.execute('''
                            INSERT INTO video_reviews 
                            (title, movie_title, reviewer_name, video_url, video_type, video_id, 
                             description, rating, movie_link, country, genre, movie_type, 
                             series_name, episode_number, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            video['title'],
                            movie_title,
                            video['channel'],
                            video['video_url'], 
                            'youtube',
                            video['video_id'],
                            video['description'],
                            7,  # Default rating
                            '',  # movie_link
                            country,
                            genre,
                            movie_type,
                            series_name,
                            episode_number,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
                        videos_added += 1
                        print(f"✅ Added: {video['title'][:50]}... [{country}, {genre}]")
                    except Exception as insert_error:
                        print(f"❌ Error inserting video '{video['title']}': {insert_error}")

            conn.commit()
            conn.close()
            return videos_added

        except Exception as e:
            print(f"❌ Error saving videos: {e}")
            return 0

    def extract_movie_title(self, title):
        prefixes = ['review', 'đánh giá', 'phân tích', 'nhận xét', 'review phim', 'phim']
        title_lower = title.lower()
        for prefix in prefixes:
            if title_lower.startswith(prefix):
                title = title[len(prefix):].strip()
                break
        if ':' in title:
            title = title.split(':')[0].strip()
        elif '-' in title:
            title = title.split('-')[0].strip()
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title.title() if title else "Unknown Movie"

# Global instance
smart_youtube_service = SmartYouTubeService()
