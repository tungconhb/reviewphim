# Services module for Web Review application
# This file makes the services directory a Python package

__version__ = "1.0.0"
__author__ = "MiniMax Agent"

# Import main services for easy access
try:
    from .auto_update_fixed import get_auto_update
    from .youtube_url_parser import YouTubeURLParser
    from .content_filter import ContentFilter
    from .smart_youtube_service import SmartYouTubeService
    
    __all__ = [
        'get_auto_update',
        'YouTubeURLParser', 
        'ContentFilter',
        'SmartYouTubeService'
    ]
except ImportError as e:
    print(f"Warning: Some services could not be imported: {e}")
    __all__ = []