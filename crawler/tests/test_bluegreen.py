"""US-5.2 — BlueGreen 蓝绿部署集成测试。"""

import pytest
from db.bluegreen import BlueGreen


@pytest.mark.usefixtures('test_meta_conn', 'test_cal_a_conn', 'test_cal_b_conn', 'patch_env')
class TestEnsureCalendarDb:
    def test_existing_returns_target_db(self):
        """已有学期 → 返回非活跃库名（b，因为 a 是活跃）"""
        with BlueGreen() as bg:
            target = bg.ensureCalendarDb(999)
        assert target == 'calendar_999_b'

    def test_existing_creates_no_new_registry_entry(self):
        """已有学期不重复注册"""
        with BlueGreen() as bg:
            bg.ensureCalendarDb(999)
            bg._use_meta()
            bg.cursor.execute(
                "SELECT COUNT(*) FROM calendar_registry WHERE calendarId = 999"
            )
            count = bg.cursor.fetchone()[0]
        assert count == 1

    def test_new_calendar_creates_dbs_and_registry(self):
        """全新学期 998 → 创建 a/b 库 + 注册 + 默认名"""
        with BlueGreen() as bg:
            target = bg.ensureCalendarDb(998)
        assert target == 'calendar_998_b'

        # 验证注册表
        import mysql.connector, os
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'mysql'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database='test_course_scheduler_meta',
            charset='utf8mb4',
        )
        c = conn.cursor()
        c.execute(
            "SELECT calendarIdI18n, active_suffix FROM calendar_registry WHERE calendarId = 998"
        )
        row = c.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == '数据同步中…'
        assert row[1] == 'a'

    def test_ensure_twice_uses_same_active(self):
        """第二次 ensure 不改变活跃面"""
        with BlueGreen() as bg:
            bg.ensureCalendarDb(999)
            bg._use_meta()
            bg.cursor.execute(
                "SELECT active_suffix FROM calendar_registry WHERE calendarId = 999"
            )
            suffix = bg.cursor.fetchone()[0]
        assert suffix == 'a'


@pytest.mark.usefixtures('test_meta_conn', 'test_cal_a_conn', 'patch_env')
class TestSwitchActiveDb:
    def test_switch_toggles_suffix(self):
        """switchActiveDb 翻转 active_suffix"""
        with BlueGreen() as bg:
            original = bg._query_active_view(999)[0]
            bg.switchActiveDb(999)
            bg._use_meta()
            bg.cursor.execute(
                "SELECT active_suffix FROM calendar_registry WHERE calendarId = 999"
            )
            toggled = bg.cursor.fetchone()[0]
        assert toggled != original
        assert toggled == 'b'
        # 恢复
        with BlueGreen() as bg:
            bg.switchActiveDb(999)


@pytest.mark.usefixtures('test_meta_conn', 'test_cal_a_conn', 'patch_env')
class TestSetCalendarName:
    def test_updates_name(self):
        """setCalendarName 更新学期中文名"""
        with BlueGreen() as bg:
            bg.setCalendarName(999, '2024-2025学年第1学期')
            bg._use_meta()
            bg.cursor.execute(
                "SELECT calendarIdI18n FROM calendar_registry WHERE calendarId = 999"
            )
            name = bg.cursor.fetchone()[0]
        assert name == '2024-2025学年第1学期'


@pytest.mark.usefixtures('test_meta_conn', 'test_cal_a_conn', 'patch_env')
class TestResetDb:
    def test_reset_truncates_all_tables(self):
        """_resetDb TRUNCATE 所有课程表"""
        with BlueGreen() as bg:
            bg.cursor.execute("USE `calendar_999_a`")
            bg.cursor.execute("INSERT INTO campus (campus, campusI18n) VALUES ('test_c', '测试校区')")
            bg.db.commit()
            bg.cursor.execute("SELECT COUNT(*) FROM campus")
            assert bg.cursor.fetchone()[0] == 1
            bg._resetDb('calendar_999_a')
            bg.cursor.execute("SELECT COUNT(*) FROM campus")
            assert bg.cursor.fetchone()[0] == 0
