"""US-5.2 — DbRouter 集成测试。需要测试 MySQL 实例。"""

import pytest

from db.router import DbRouter


@pytest.mark.usefixtures('test_meta_conn', 'test_cal_a_conn', 'patch_env')
class TestDbRouter:
    def test_resolve_db_returns_active_db(self):
        """resolve_db(999) → calendar_999_a（active_suffix='a'）"""
        r = DbRouter()
        db_name = r.resolve_db(999)
        assert db_name == 'calendar_999_a'

    def test_resolve_db_nonexistent_raises(self):
        """不存在的学期 → ValueError"""
        r = DbRouter()
        with pytest.raises(ValueError, match='未在 calendar_registry 注册'):
            r.resolve_db(404)

    def test_get_connection_works(self):
        """get_connection 返回可用连接，且指向正确数据库"""
        r = DbRouter()
        conn = r.get_connection(999)
        c = conn.cursor()
        c.execute('SELECT DATABASE()')
        db = c.fetchone()[0]
        conn.close()
        assert db == 'calendar_999_a'

    def test_pool_caching(self):
        """同一 calendarId 的 pool 被复用"""
        r = DbRouter()
        pool1 = r.get_pool(999)
        pool2 = r.get_pool(999)
        assert pool1 is pool2

    def test_second_instance_creates_new_router(self):
        """新 DbRouter 实例应该独立管理 pools"""
        r1 = DbRouter()
        r2 = DbRouter()
        assert r1._pools is not r2._pools
