"""
Auto-Update Service - Fixed Version
Hệ thống cập nhật tự động video review
"""

import sqlite3
from datetime import datetime
import config

class AutoUpdateService:
    def __init__(self):
        self.init_auto_update_tables()

    def init_auto_update_tables(self):
        """Initialize auto-update tables"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()

            # Create update logs table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    message TEXT,
                    videos_found INTEGER DEFAULT 0,
                    videos_added INTEGER DEFAULT 0
                )
            ''')

            # Create auto-update settings table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_update_settings (
                    id INTEGER PRIMARY KEY,
                    enabled BOOLEAN DEFAULT 1,
                    last_update TIMESTAMP,
                    update_interval_hours INTEGER DEFAULT 24,
                    max_videos_per_run INTEGER DEFAULT 20,
                    auto_publish BOOLEAN DEFAULT 1
                )
            ''')

            # Insert default settings if not exists
            cursor.execute('SELECT COUNT(*) FROM auto_update_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO auto_update_settings 
                    (id, enabled, update_interval_hours, max_videos_per_run, auto_publish)
                    VALUES (1, 1, 24, 20, 1)
                ''')

            conn.commit()
            conn.close()
            print("✅ Auto-update tables initialized")

        except Exception as e:
            print(f"❌ Error initializing auto-update tables: {e}")

    def get_stats(self):
        """Get auto-update statistics"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()

            # Get settings
            cursor.execute('SELECT * FROM auto_update_settings WHERE id = 1')
            settings = cursor.fetchone()

            # Get total videos
            cursor.execute('SELECT COUNT(*) FROM video_reviews')
            total_videos = cursor.fetchone()[0]

            # Get last successful update
            cursor.execute('''
                SELECT timestamp, videos_found, videos_added
                FROM update_logs 
                WHERE status = 'SUCCESS'
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            last_success = cursor.fetchone()

            conn.close()

            return {
                'enabled': bool(settings[1]) if settings else True,
                'last_update': settings[2] if settings else None,
                'total_videos_added': total_videos,
                'last_successful_update': {
                    'timestamp': last_success[0] if last_success else None,
                    'videos_found': last_success[1] if last_success else 0,
                    'videos_added': last_success[2] if last_success else 0
                } if last_success else None
            }

        except Exception as e:
            print(f"❌ Error getting auto-update stats: {e}")
            return {
                'enabled': False,
                'total_videos_added': 0,
                'last_successful_update': None
            }

    def enable(self):
        """Enable auto-update"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            cursor.execute('UPDATE auto_update_settings SET enabled = 1 WHERE id = 1')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error enabling auto-update: {e}")
            return False

    def disable(self):
        """Disable auto-update"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            cursor.execute('UPDATE auto_update_settings SET enabled = 0 WHERE id = 1')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error disabling auto-update: {e}")
            return False

    def run_update(self):
        """Run manual update"""
        try:
            # Import smart youtube service to generate new videos
            from services.smart_youtube_service import SmartYouTubeService
            
            smart_service = SmartYouTubeService()
            result = smart_service.fetch_and_add_videos()
            
            # Log the update
            self.log_update('SUCCESS', f'Manual update completed', result.get('found', 0), result.get('added', 0))
            
            return result
            
        except Exception as e:
            print(f"❌ Error running manual update: {e}")
            self.log_update('ERROR', f'Manual update failed: {str(e)}', 0, 0)
            return {'found': 0, 'added': 0, 'error': str(e)}

    def log_update(self, status, message, videos_found, videos_added):
        """Log update activity"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO update_logs (status, message, videos_found, videos_added)
                VALUES (?, ?, ?, ?)
            ''', (status, message, videos_found, videos_added))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error logging update: {e}")

    def get_recent_logs(self, limit=10):
        """Get recent logs"""
        try:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, status, message, videos_found, videos_added
                FROM update_logs 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            logs = cursor.fetchall()
            conn.close()
            
            return logs
            
        except Exception as e:
            print(f"❌ Error getting logs: {e}")
            return []

# Global instance
_auto_update_instance = None

def get_auto_update(app=None):
    """Get or create auto-update instance"""
    global _auto_update_instance
    if _auto_update_instance is None:
        _auto_update_instance = AutoUpdateService()
    return _auto_update_instance