"""数据库路由器 — 根据 calendarId 解析活跃学期库，按需创建连接池。

蓝绿切换（active_suffix 翻转）后，Redis Pub/Sub 监听线程（utils/pool_refresh.py）
会调用 invalidate_pool() 丢弃旧池，下次请求自动按新 registry 重建。
"""

import os
import threading

import mysql.connector


class DbRouter:
    """管理元数据库 + 各学期库的连接池。"""

    def __init__(self):
        self._meta_pool = None
        self._pools = {}  # calendarId → MySQLConnectionPool
        self._lock = threading.RLock()

    def _create_pool(self, pool_name, pool_size, database):
        return mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_R_USER'),
            password=os.getenv('DB_R_PASSWORD'),
            database=database,
            port=int(os.getenv('DB_PORT')),
            charset='utf8mb4',
        )

    @property
    def meta_pool(self):
        if self._meta_pool is None:
            with self._lock:
                if self._meta_pool is None:
                    self._meta_pool = self._create_pool(
                        'meta', 3, os.getenv('DB_META'))
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
        """获取指定学期的连接池（懒创建，加锁避免并发重复建池）。"""
        with self._lock:
            pool = self._pools.get(calendar_id)
            if pool is None:
                db_name = self.resolve_db(calendar_id)
                pool = self._create_pool(f'cal_{calendar_id}', 5, db_name)
                self._pools[calendar_id] = pool
            return pool

    def invalidate_pool(self, calendar_id):
        """蓝绿切换后丢弃旧连接池，下次 get_pool 重新解析 registry 并重建。

        只 pop 不关闭旧池连接：在途请求（已拿到旧池引用）可继续跑完，
        不会撞上空队列报 PoolError；旧池引用归零后被 GC，底层 socket
        随之关闭（最多池大小条连接滞留数秒，无泄漏）。
        """
        with self._lock:
            self._pools.pop(calendar_id, None)

    def get_connection(self, calendar_id):
        """获取指定学期活跃库的连接。"""
        return self.get_pool(calendar_id).get_connection()


# 全局单例
router = DbRouter()
