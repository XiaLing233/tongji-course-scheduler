"""数据库连接基类。"""

import os

import mysql.connector


class Connection:
    """MySQL 连接上下文。默认连元数据库，指定 database 则连学期库。"""

    def __init__(self, database=None):
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=database or os.getenv('DB_META'),
            port=int(os.getenv('DB_PORT')),
            charset='utf8mb4',
        )
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.db.close()

    def _use_meta(self):
        self.cursor.execute(f"USE `{os.getenv('DB_META', 'course_scheduler_meta')}`")

    def _query_active_view(self, calendarId):
        """查 active_calendars 视图 → (active_suffix, db_name, calendarIdI18n) 或 None。"""
        self._use_meta()
        self.cursor.execute(
            "SELECT active_suffix, db_name, calendarIdI18n "
            "FROM active_calendars WHERE calendarId = %s",
            (calendarId,)
        )
        return self.cursor.fetchone()
