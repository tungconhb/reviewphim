"""
Content Filter và Duplicate Detection System
Hệ thống lọc nội dung và phát hiện trùng lặp video
"""

import sqlite3
import re
from datetime import datetime
from difflib import SequenceMatcher
import config


class ContentFilter:
    """Hệ thống lọc và kiểm tra trùng lặp video"""
    
    def __init__(self):
        print("🔧 Content Filter initialized")
    
    def calculate_text_similarity(self, text1, text2):
        """Tính độ tương đồng giữa 2 chuỗi text"""
        # Normalize text
        text1 = self.normalize_text(text1)
        text2 = self.normalize_text(text2)
        
        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, text1, text2).ratio()
        return similarity
    
    def normalize_text(self, text):
        """Chuẩn hóa text để so sánh"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra spaces and special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_movie_name(self, title):
        """Trích xuất tên phim từ tiêu đề review"""
        title = title.lower()
        
        # Remove common prefixes
        prefixes = ['review', 'đánh giá', 'review phim', 'phim', 'critique', 'vus review', 'vus']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Extract movie name (before dash or colon)
        if ':' in title:
            title = title.split(':')[0].strip()
        elif '-' in title:
            title = title.split('-')[0].strip()
        
        # Clean up
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title.title()
    
    def is_duplicate_video(self, new_video, existing_videos):
        """Kiểm tra xem video mới có trùng với video đã có không"""
        new_title = new_video.get('title', '')
        new_video_id = new_video.get('video_id', '')
        new_channel = new_video.get('channel_title', '')
        new_desc = new_video.get('description', '')
        
        new_movie = self.extract_movie_name(new_title)
        
        for existing in existing_videos:
            # If it's from database (tuple format)
            if isinstance(existing, tuple) and len(existing) >= 7:
                existing_title = existing[1]  # title
                existing_video_id = existing[6]  # video_id
                existing_channel = existing[3]  # reviewer_name
                existing_desc = existing[7] if len(existing) > 7 else ""  # description
            # If it's from video list (dict format)
            elif isinstance(existing, dict):
                existing_title = existing.get('title', '')
                existing_video_id = existing.get('video_id', '')
                existing_channel = existing.get('channel_title', '')
                existing_desc = existing.get('description', '')
            else:
                continue
            
            # Check exact video ID match first
            if new_video_id and existing_video_id and new_video_id == existing_video_id:
                print(f"🚫 Duplicate detected - Same video ID: {new_video_id}")
                return True
            
            # Calculate similarities
            title_similarity = self.calculate_text_similarity(new_title, existing_title)
            desc_similarity = self.calculate_text_similarity(new_desc, existing_desc)
            
            existing_movie = self.extract_movie_name(existing_title)
            movie_similarity = self.calculate_text_similarity(new_movie, existing_movie)
            
            same_channel = new_channel.lower() == existing_channel.lower() if new_channel and existing_channel else False
            
            is_duplicate = False
            
            # Very high title similarity
            if title_similarity > config.TITLE_SIMILARITY_THRESHOLD:
                is_duplicate = True
                print(f"🚫 Duplicate detected - High title similarity: {title_similarity:.2f}")
            
            # Same movie + same channel
            elif movie_similarity > 0.8 and same_channel:
                is_duplicate = True
                print(f"🚫 Duplicate detected - Same movie ({movie_similarity:.2f}) + Same channel")
            
            # High description similarity
            elif desc_similarity > config.SIMILARITY_THRESHOLD:
                is_duplicate = True
                print(f"🚫 Duplicate detected - High description similarity: {desc_similarity:.2f}")
            
            # Multiple moderate similarities
            elif (title_similarity > 0.6 and movie_similarity > 0.7) or \
                 (title_similarity > 0.6 and desc_similarity > 0.6):
                is_duplicate = True
                print(f"🚫 Duplicate detected - Multiple similarities (T:{title_similarity:.2f}, M:{movie_similarity:.2f}, D:{desc_similarity:.2f})")
            
            if is_duplicate:
                print(f"   New: {new_title[:50]}...")
                print(f"   Existing: {existing_title[:50]}...")
                return True
        
        return False
    
    def get_existing_videos_from_db(self):
        """Lấy danh sách video đã có trong database"""
        try:
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM video_reviews ORDER BY created_at DESC LIMIT 1000")
            videos = cursor.fetchall()
            
            conn.close()
            return videos
            
        except Exception as e:
            print(f"❌ Error getting existing videos: {e}")
            return []
    
    def filter_duplicates(self, new_videos):
        """Lọc bỏ video trùng lặp từ danh sách videos mới"""
        print(f"🔍 Filtering duplicates from {len(new_videos)} new videos...")
        
        # Get existing videos from database
        existing_videos = self.get_existing_videos_from_db()
        print(f"📊 Comparing against {len(existing_videos)} existing videos")
        
        filtered_videos = []
        duplicate_count = 0
        
        for i, video in enumerate(new_videos):
            print(f"\n⚡ Checking video {i+1}/{len(new_videos)}: {video['title'][:50]}...")
            
            # Check against existing videos
            if not self.is_duplicate_video(video, existing_videos):
                # Also check against other new videos (avoid duplicates within the same batch)
                if not self.is_duplicate_video(video, filtered_videos):
                    filtered_videos.append(video)
                    print(f"✅ Video accepted")
                else:
                    duplicate_count += 1
                    print(f"🚫 Duplicate within new batch")
            else:
                duplicate_count += 1
        
        print(f"\n📊 Filtering results:")
        print(f"   Original: {len(new_videos)} videos")
        print(f"   Filtered: {len(filtered_videos)} videos")
        print(f"   Duplicates removed: {duplicate_count} videos")
        
        return filtered_videos
    
    def is_movie_review_video(self, video):
        """Kiểm tra xem video có phải là review phim (bao gồm Vus Review) không"""
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Các từ khóa tích cực cho review phim (bao gồm Vus Review)
        review_keywords = [
            'review', 'đánh giá', 'nhận xét', 'phân tích', 'critique',
            'review phim', 'đánh giá phim', 'phim hay', 'phim mới',
            'spoiler', 'trailer reaction', 'breakdown', 'ending explained',
            'tóm tắt phim', 'giải thích phim', 'kết thúc phim',
            # Thêm Vus Review keywords
            'vus', 'vus review', 'vus đánh giá', 'vus phim', 'vus cinema',
            'vus trailer', 'vus movie', 'vus film', 'vus spoiler',
            'vus breakdown', 'vus ending', 'vus reaction'
        ]
        
        # Các từ khóa phim ảnh
        movie_keywords = [
            'phim', 'movie', 'film', 'cinema', 'tập', 'episode', 'season',
            'marvel', 'dc', 'disney', 'netflix', 'hollywood', 'bollywood',
            'anime', 'drama', 'series', 'thriller', 'horror', 'comedy',
            'action', 'romance', 'sci-fi'
        ]
        
        # Kiểm tra có từ khóa review và phim
        has_review_keyword = any(keyword in combined_text for keyword in review_keywords)
        has_movie_keyword = any(keyword in combined_text for keyword in movie_keywords)
        
        # Vẫn giữ logic loại trừ các video không phù hợp nhưng điều chỉnh cho Vus
        excluded_keywords = [
            'trailer chính thức', 'official trailer', 'teaser',
            'behind the scene', 'making of', 'gala', 'thảm đỏ',
            'interview', 'hậu trường', 'news', 'tin tức',
            r'\bgame\b', r'\bgameplay\b', r'\bwalkthrough\b', r'\bspeedrun\b',  # Word boundaries để tránh false positive
            'music video', 'mv', 'live stream',
            'unboxing', 'vlog', 'daily',
            'reaction only'
        ]
        
        # Check excluded keywords with regex for word boundaries
        has_excluded = False
        for keyword in excluded_keywords:
            if keyword.startswith(r'\b') and keyword.endswith(r'\b'):
                # Use regex for word boundary check
                import re
                if re.search(keyword, combined_text):
                    has_excluded = True
                    break
            else:
                # Normal substring check
                if keyword in combined_text:
                    has_excluded = True
                    break
        
        # Kết quả: phải có từ khóa review VÀ phim, và KHÔNG có từ khóa loại trừ
        is_movie_review = has_review_keyword and has_movie_keyword and not has_excluded
        
        if not is_movie_review:
            reason = []
            if not has_review_keyword:
                reason.append("no review keywords")
            if not has_movie_keyword:
                reason.append("no movie keywords")
            if has_excluded:
                reason.append("has excluded keywords")
            print(f"❌ Not a movie review: {' + '.join(reason)}")
        
        return is_movie_review

    def validate_video_quality(self, video):
        """Kiểm tra chất lượng video trước khi thêm"""
        issues = []
        
        # Check if it's a movie review video first
        if not self.is_movie_review_video(video):
            issues.append('Not a movie review video')
        
        # Check title length
        if len(video['title']) < 10:
            issues.append('Title too short')
        
        # Check if has movie title
        movie_title = self.extract_movie_name(video['title'])
        if len(movie_title) < 2:
            issues.append('Cannot extract movie name')
        
        # Check view count
        if video.get('view_count', 0) < config.MIN_VIEWS:
            issues.append(f'Low view count: {video.get("view_count", 0)}')
        
        # Check duration - giữ min 10 phút, bỏ giới hạn max
        duration = video.get('duration', 0)
        if duration < config.MIN_VIDEO_DURATION:
            issues.append(f'Too short: {duration}s (minimum {config.MIN_VIDEO_DURATION}s)')
        # Bỏ check max duration vì MAX_VIDEO_DURATION = 0 (unlimited)
        if config.MAX_VIDEO_DURATION > 0 and duration > config.MAX_VIDEO_DURATION:
            issues.append(f'Too long: {duration}s (maximum {config.MAX_VIDEO_DURATION}s)')
        
        # Check channel name
        if not video.get('channel_title'):
            issues.append('Missing channel name')
        
        if issues:
            print(f"⚠️ Quality issues for '{video['title'][:30]}...': {', '.join(issues)}")
            return False
        
        return True
    
    def process_videos(self, videos):
        """Main method để xử lý và lọc videos"""
        print(f"\n🎯 Processing {len(videos)} videos...")
        
        # Step 1: Validate quality
        print("\n📋 Step 1: Quality validation...")
        quality_videos = []
        for video in videos:
            if self.validate_video_quality(video):
                quality_videos.append(video)
        
        print(f"✅ {len(quality_videos)} videos passed quality check")
        
        # Step 2: Remove duplicates
        print("\n🔍 Step 2: Duplicate detection...")
        final_videos = self.filter_duplicates(quality_videos)
        
        print(f"\n🎉 Final result: {len(final_videos)} unique, high-quality videos ready to add!")
        
        return final_videos


if __name__ == "__main__":
    # Test the content filter
    filter_system = ContentFilter()
    
    # Test similarity
    text1 = "Review phim Avengers Endgame - Cái kết hoàn hảo"
    text2 = "Đánh giá phim Avengers: Endgame - Kết thúc tuyệt vời"
    
    similarity = filter_system.calculate_text_similarity(text1, text2)
    print(f"Similarity: {similarity:.2f}")
    
    # Test movie extraction
    movie1 = filter_system.extract_movie_name(text1)
    movie2 = filter_system.extract_movie_name(text2)
    print(f"Movie 1: {movie1}")
    print(f"Movie 2: {movie2}")