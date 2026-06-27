"""US-5.3 — Flask API 端点集成测试。"""

import json

import mysql.connector
import pytest

from app import app


# ================================================================
#  测试数据填充
# ================================================================

@pytest.fixture(scope='session')
def seed_data(db_config, test_meta_conn, test_cal_a_conn):
    """向 test_calendar_999_a 填充维度、课程、教师、专业数据。"""
    db = test_cal_a_conn
    c = db.cursor()
    c.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 维度（值来自真实数据库）
    c.execute("INSERT IGNORE INTO assessment VALUES (1, '考试'), (2, '考查')")
    c.execute("INSERT IGNORE INTO campus VALUES (1, '四平路校区'), (3, '嘉定校区'), (4, '沪西校区')")
    c.execute("INSERT IGNORE INTO coursenature VALUES (325, '人文经典与审美素养'), (848, '通识选修课'), (958, '科学探索与生命关怀')")
    c.execute("INSERT IGNORE INTO faculty VALUES ('000034', '职业技术教育学院'), ('000050', '电子与信息工程学院'), ('000285', '其他学院')")
    c.execute("INSERT IGNORE INTO language VALUES (1, '中文'), (8, '英语')")

    # 课程
    c.execute("INSERT INTO coursedetail "
              "(id, code, name, courseLabelId, assessmentMode, campus, "
              "courseCode, courseName, credit, teachingLanguage, faculty) "
              "VALUES "
              "(1001, '34001201', '01班', 325, 1, 1, '340012', '测试课程A', 3.0, 1, '000034'),"
              "(1002, '34001202', '02班', 325, 2, 3, '340012', '测试课程A', 3.0, 1, '000034'),"
              "(1003, '14007601', '01班', 958, 1, 1, '140076', '公共营养学', 1.5, 1, '000285'),"
              "(1004, '99900001', '01班', 848, 2, 1, '999000', '测试选修课', 2.0, 1, '000034')")

    # 教师
    c.execute("INSERT INTO teacher VALUES "
              "(200000000001, 1001, '13060', '李华', '李华(13060) 星期一3-4节 [1-16] A楼101\\n'),"
              "(200000000002, 1002, '13061', '王五', '王五(13061) 星期二5-6节 [1-16] B楼201\\n'),"
              "(200000000003, 1003, '05222', '关佶红', '关佶红(05222) 星期一3-4节 [1-17] 南129\\n')")

    # 专业
    c.execute("INSERT INTO major (id, code, grade, name) VALUES "
              "(1, '10054', 2023, '2023(10054 计算机科学与技术)')")
    c.execute("INSERT INTO majorandcourse (majorId, courseId) VALUES (1, 1001)")

    db.commit()

    # 元数据库 — fetchlog
    mc = test_meta_conn.cursor()
    mc.execute("INSERT INTO fetchlog (calendarId, startTime, endTime, status, totalCourses, totalPages) "
               "VALUES (999, '2026-06-01 08:00:00', '2026-06-01 08:30:00', 'completed', 1000, 5)")
    test_meta_conn.commit()

    yield

    mc.execute("DELETE FROM fetchlog WHERE calendarId = 999")
    test_meta_conn.commit()


# ================================================================
#  Flask test client
# ================================================================

@pytest.fixture
def client(patch_env):
    """Flask test client（DB_META 已切到测试库）。"""
    app.config['TESTING'] = True
    return app.test_client()


# ================================================================
#  API 端点测试
# ================================================================

class TestHealth:
    def test_health_ok(self, client, test_meta_conn):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        assert resp.json['code'] == 200


class TestCalendars:
    def test_get_calendars(self, client, seed_data):
        resp = client.get('/api/calendars')
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 1
        assert resp.json['data'][0]['calendarId'] == 999


class TestCampuses:
    def test_get_campuses(self, client, seed_data):
        resp = client.get('/api/calendars/999/campuses')
        assert resp.status_code == 200
        names = [c['campusName'] for c in resp.json['data']]
        assert '四平路校区' in names
        assert '嘉定校区' in names


class TestFaculties:
    def test_get_faculties(self, client, seed_data):
        resp = client.get('/api/calendars/999/faculties')
        assert resp.status_code == 200
        names = [f['facultyName'] for f in resp.json['data']]
        assert '电子与信息工程学院' in names


class TestGrades:
    def test_get_grades(self, client, seed_data):
        resp = client.get('/api/calendars/999/grades')
        assert resp.status_code == 200
        assert 'gradeList' in resp.json['data']


class TestMajors:
    def test_get_majors(self, client, seed_data):
        resp = client.get('/api/calendars/999/grades/2023/majors')
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 1
        assert resp.json['data'][0]['code'] == '10054'


class TestCourses:
    def test_courses_by_major(self, client, seed_data):
        resp = client.get('/api/calendars/999/courses?grade=2023&major=10054')
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 1

    def test_courses_by_nature_ids(self, client, seed_data):
        resp = client.get('/api/calendars/999/courses?natureIds=958')
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 1
        assert resp.json['data'][0]['courseLabelId'] == 958

    def test_courses_by_day_section(self, client, seed_data):
        resp = client.get('/api/calendars/999/courses?day=1&section=1')
        assert resp.status_code == 200

    def test_courses_invalid_params(self, client, seed_data):
        resp = client.get('/api/calendars/999/courses')
        assert resp.status_code == 400


class TestCourseTypes:
    def test_course_types(self, client, seed_data):
        resp = client.get('/api/calendars/999/course-types')
        assert resp.status_code == 200
        assert len(resp.json['data']) >= 2


class TestCourseDetails:
    def test_batch_details(self, client, seed_data):
        resp = client.post('/api/calendars/999/courses/details',
                           json={'courseCodes': ['340012']})
        assert resp.status_code == 200
        assert '340012' in resp.json['data']

    def test_batch_details_empty(self, client):
        resp = client.post('/api/calendars/999/courses/details',
                           json={'courseCodes': []})
        assert resp.status_code == 400


class TestSearch:
    def test_search_by_name(self, client, seed_data):
        resp = client.post('/api/calendars/999/courses/search',
                           json={'courseName': '测试'})
        assert resp.status_code == 200
        assert 'courses' in resp.json['data']


class TestUpdateTime:
    def test_update_time(self, client, seed_data):
        resp = client.get('/api/calendars/999/update-time')
        assert resp.status_code == 200
        assert resp.json['data'] is not None


class TestSyncBatch:
    def test_batch(self, client, seed_data):
        resp = client.post('/api/calendars/999/courses/batch',
                           json={'majorCourseCodes': ['340012'],
                                 'otherCourseCodes': ['140076'],
                                 'majorInfo': {'grade': 2023, 'code': '10054'}})
        assert resp.status_code == 200
        assert '340012' in resp.json['data']
        assert '140076' in resp.json['data']

    def test_batch_missing_body(self, client):
        resp = client.post('/api/calendars/999/courses/batch',
                           content_type='application/json')
        assert resp.status_code == 400
