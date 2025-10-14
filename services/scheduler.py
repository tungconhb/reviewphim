"""
Auto-Update Scheduler Service
Quản lý lịch trình auto-update video từ YouTube API
"""

import threading
import time
import sqlite3
from datetime import datetime
import config


class SchedulerService:
    def __init__(self):
        self.running = False
        self.thread = None
        self.interval_hours = config.UPDATE_INTERVAL_HOURS
        self._lock = threading.Lock()

    def start_scheduler(self):
        """Start background scheduler"""
        if self.running:
            print("⏸️ Scheduler already running.")
            return

        print("🚀 Starting auto-update scheduler...")
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler)
        self.thread.daemon = True
        self.thread.start()

    def stop_scheduler(self):
        """Stop background scheduler"""
        print("🛑 Stopping scheduler...")
        self.running = False

    def run_scheduler(self):
        """Main loop for auto-update"""
        while self.running:
            print(f"🕒 Running scheduled update at {datetime.now()}")
            self.run_auto_update()
            print(f"✅ Next run in {self.interval_hours} hours")
            time.sleep(self.interval_hours * 3600)

    def run_auto_update(self):
        """Chạy auto-update với demo YouTube crawler"""
        try:
            with self._lock:
                print("🔍 Bắt đầu tìm kiếm video mới với Smart YouTube Service...")
                
                # Sử dụng Smart YouTube Service thay vì demo
                from services.smart_youtube_service import smart_youtube_service
                videos_found, videos_added = smart_youtube_service.run_smart_fetch()
                
                print(f"✅ Hoàn thành: Tìm thấy {videos_found}, thêm {videos_added} videos")
                
                self.log_update_activity("SUCCESS", f"Tìm thấy {videos_found} videos, thêm {videos_added} videos mới", videos_found, videos_added)
        except Exception as e:
            self.log_update_activity("ERROR", f"Lỗi auto-update: {str(e)}")
            print(f"❌ Auto-update failed: {e}")

    def run_manual_update(self):
        """Run manual update triggered by admin"""
        print("🟢 Manual update triggered by admin...")
        self.run_auto_update()

    def log_update_activity(self, status, message, videos_found=0, videos_added=0):
        """Log update activity to database"""
        try:
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()

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

            cursor.execute(
                '''INSERT INTO update_logs (status, message, videos_found, videos_added)
                   VALUES (?, ?, ?, ?)''',
                (status, message, videos_found, videos_added)
            )

            conn.commit()
            conn.close()
            print(f"🗒️ Logged update: {status} — {message}")

        except Exception as e:
            print(f"❌ Error logging update: {e}")

    def get_recent_logs(self, limit=20):
        """Get recent update logs"""
        try:
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT timestamp, status, message, videos_found, videos_added
                   FROM update_logs
                   ORDER BY timestamp DESC
                   LIMIT ?''',
                (limit,)
            )
            logs = cursor.fetchall()
            conn.close()
            return logs
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return []

    def get_scheduler_status(self):
        """Get current scheduler status"""
        return "running" if self.running else "stopped"


# Global instance
_scheduler_instance = None


def get_scheduler():
    """Return singleton instance of scheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
