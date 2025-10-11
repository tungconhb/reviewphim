# Auto-Update Configuration

# YouTube API Configuration
YOUTUBE_API_KEY = 'AIzaSyAfHAqWWNGZPpkelphX81lxoIDZ31rnPPE'  # ✅ API KEY THẬT ĐÃ CẬP NHẬT
# API key được cung cấp để update video thật

# Search Configuration - Added Vus Review to existing channels
SEARCH_QUERIES = [
    'Chơi Phim Review',
    'NiNi Mê Phim', 
    'Mèo Mê Phim',
    'PIKACHU Review Phim',
    'Ớt Review Phim',
    'All In One Movie',
    'FC Review',
    'Vus Review',  # Thêm Vus Review vào danh sách
    'Vus Review phim',
    'Chú Cuội Review Phim',
    'Review phim Nguyễn Review 2',
    'Review phim Cuồng Phim Hay',
    'Review phim Chén Phim Review',
    'Review phim Động Phim Review'
]

# Content Filter Settings
MIN_VIDEO_DURATION = 600  # Khôi phục lại 10 phút minimum
MAX_VIDEO_DURATION = 0  # ✅ BỎ GIỚI HẠN ĐỘ DÀI TỐI ĐA (0 = unlimited)
MIN_VIEWS = 100  # Minimum view count
MIN_LIKES = 5   # Minimum like count

# Duplicate Detection
SIMILARITY_THRESHOLD = 0.75  # 75% similarity = duplicate
TITLE_SIMILARITY_THRESHOLD = 0.80  # 80% title similarity = duplicate

# Scheduler Settings
UPDATE_INTERVAL_HOURS = 24  # Run every 24 hours
MAX_NEW_VIDEOS_PER_RUN = 20  # Maximum new videos to add per run

# Vietnamese Channels (Add more as needed)
PREFERRED_CHANNELS = [
    'UCl7mAGnY4jh4Ps8rhhh8XZQ',  # Example channel ID
    'UC_x5XG1OV2P6uZZ5FSM9Ttw',  # Add real Vietnamese channel IDs
    # Add more channel IDs of Vietnamese movie reviewers
]

# Blacklisted Keywords (to avoid spam/inappropriate content)
BLACKLISTED_KEYWORDS = [
    'cam',
    'lậu',
    'download',
    'link phim',
    'full hd free',
    'hack',
    'crack'
]

# Language Detection
REQUIRED_LANGUAGE = 'vi'  # Vietnamese
LANGUAGE_CONFIDENCE_THRESHOLD = 0.7

# Database
DATABASE_PATH = 'db.sqlite'

# Auto-publish settings
AUTO_PUBLISH = True  # Set to False if you want manual approval
DEFAULT_RATING = 7   # Default rating for auto-added videos

print("✅ Auto-Update Configuration loaded!")
