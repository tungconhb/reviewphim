import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langdetect import detect, LangDetectException

import config

# Use API key from config file
YOUTUBE_API_KEY = config.YOUTUBE_API_KEY

# Use search queries from config file  
SEARCH_QUERIES = config.SEARCH_QUERIES

def get_youtube_service():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def extract_video_info(item):
    video_id = item["id"]["videoId"]
    snippet = item["snippet"]
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
        or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    )

    return {
        "video_id": video_id,
        "title": snippet["title"],
        "channel_title": snippet["channelTitle"],
        "published_at": snippet["publishedAt"],
        "thumbnail": thumbnail_url,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
    }

def crawl_videos():
    service = get_youtube_service()
    all_videos = []

    for query in SEARCH_QUERIES:
        try:
            request = service.search().list(
                q=query, part="snippet", type="video", maxResults=10, order="date"
            )
            response = request.execute()
            for item in response.get("items", []):
                try:
                    video = extract_video_info(item)
                    all_videos.append(video)
                except Exception:
                    continue
        except HttpError as e:
            print(f"❌ API error: {e}")
            continue

    return all_videos
