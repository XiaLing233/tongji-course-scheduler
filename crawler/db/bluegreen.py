"""蓝绿部署 + 同步日志 + 数据库管理。"""

import os
from pathlib import Path

import mysql.connector

from db.connection import Connection

# 学期库 DDL — 仅用于 _createCalendarDbs（首次创建新学期）
_COURSE_DDL = (Path(__file__).resolve().parent.parent / 'course_template.sql').read_text(encoding='utf-8')


class BlueGreen(Connection):
    """蓝绿部署：建库、切换、日志。"""

    # ---- 数据库生命周期 ----

    def _ensure_readonly_user(self):
        r_user = os.getenv('DB_R_USER', 'readonly')
        r_pass = os.getenv('DB_R_PASSWORD', 'readonly')
        meta = os.getenv('DB_META', 'course_scheduler_meta')
        try:
            self.cursor.execute(
                f"CREATE USER IF NOT EXISTS '{r_user}'@'%' IDENTIFIED BY %s", (r_pass,)
            )
            self.cursor.execute(f"GRANT SELECT ON `{meta}`.* TO '{r_user}'@'%'")
        except mysql.connector.Error:
            pass

    def _createCalendarDbs(self, calendarId):
        """创建 calendar_{id}_a / calendar_{id}_b（仅首次）。"""
        r_user = os.getenv('DB_R_USER', 'readonly')
        self._ensure_readonly_user()

        for suffix in ('a', 'b'):
            db_name = f"calendar_{calendarId}_{suffix}"
            self.cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            self.cursor.execute(f"USE `{db_name}`")
            for stmt in _COURSE_DDL.split(';'):
                stmt = stmt.strip()
                if stmt:
                    self.cursor.execute(stmt)
            self.cursor.execute(f"GRANT SELECT ON `{db_name}`.* TO '{r_user}'@'%'")
        self.db.commit()

    def _resetDb(self, db_name):
        """TRUNCATE 所有表，保留结构和 GRANT。"""
        self.cursor.execute(f"USE `{db_name}`")
        self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in ('majorandcourse', 'teacher', 'coursedetail',
                      'major', 'language', 'faculty', 'coursenature', 'campus', 'assessment'):
            self.cursor.execute(f"TRUNCATE TABLE {table}")
        self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        self.db.commit()

    # ---- 蓝绿操作 ----

    def ensureCalendarDb(self, calendarId, calendarName=None):
        """注册 → TRUNCATE 非活跃库 → 返回目标数据库名。"""
        row = self._query_active_view(calendarId)

        if row is None:
            self._createCalendarDbs(calendarId)
            self._use_meta()
            self.cursor.execute(
                "INSERT INTO calendar_registry (calendarId, calendarIdI18n) VALUES (%s, %s)",
                (calendarId, calendarName or f"Calendar {calendarId}")
            )
            self.db.commit()
            active = 'a'
        else:
            active = row[0]

        inactive = 'b' if active == 'a' else 'a'
        target_db = f"calendar_{calendarId}_{inactive}"
        self._resetDb(target_db)
        return target_db

    def switchActiveDb(self, calendarId):
        """蓝绿切换：翻转 active_suffix。"""
        self._use_meta()
        self.cursor.execute(
            "UPDATE calendar_registry "
            "SET active_suffix = IF(active_suffix = 'a', 'b', 'a') "
            "WHERE calendarId = %s",
            (calendarId,)
        )
        self.db.commit()

    def getActiveDbName(self, calendarId):
        row = self._query_active_view(calendarId)
        return row[1] if row else None

    def calendarIdToText(self, calendarId):
        row = self._query_active_view(calendarId)
        return row[2] if row else None
