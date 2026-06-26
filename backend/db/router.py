"""数据库路由器 — 根据 calendarId 解析活跃学期库，按需创建连接池。"""

import os

import mysql.connector


class DbRouter:
    """管理元数据库 + 各学期库的连接池。"""

    def __init__(self):
        self._meta_pool = None
        self._pools = {}  # calendarId → MySQLConnectionPool

    @property
    def meta_pool(self):
        if self._meta_pool is None:
            self._meta_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name='meta',
                pool_size=3,
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_R_USER'),
                password=os.getenv('DB_R_PASSWORD'),
                database=os.getenv('DB_META'),
                port=int(os.getenv('DB_PORT')),
                charset='utf8mb4',
            )
        return self._meta_pool

    def resolve_db(self, calendar_id):
        """calendarId → 活跃数据库名（查 active_calendars 视图）。"""
        conn = self.meta_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT db_name FROM active_calendars WHERE calendarId = %s",
                (calendar_id,)
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"学期 {calendar_id} 未在 calendar_registry 注册")
            return row[0]
        finally:
            conn.close()

    def get_pool(self, calendar_id):
        """获取指定学期的连接池（懒创建）。"""
        if calendar_id not in self._pools:
            db_name = self.resolve_db(calendar_id)
            self._pools[calendar_id] = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=f'cal_{calendar_id}',
                pool_size=5,
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_R_USER'),
                password=os.getenv('DB_R_PASSWORD'),
                database=db_name,
                port=int(os.getenv('DB_PORT')),
                charset='utf8mb4',
            )
        return self._pools[calendar_id]

    def get_connection(self, calendar_id):
        """获取指定学期活跃库的连接。"""
        return self.get_pool(calendar_id).get_connection()


# 全局单例
router = DbRouter()
