"""US-5.2 — insertTeachers 教师姓名补全集成测试。"""

import pytest
from db.inserter import CourseInserter


@pytest.fixture
def inserter(test_cal_a_conn, patch_env):
    """连接到 test_calendar_999_a 的 CourseInserter，预填 FK 依赖。"""
    ins = CourseInserter(database='calendar_999_a')
    # 填充维度表（teacher → coursedetail → campus/language/... FK 链）
    for table, cols, vals in [
        ('assessment', ('assessmentMode', 'assessmentModeI18n'), ('exam', '考试')),
        ('campus', ('campus', 'campusI18n'), ('siping', '四平路校区')),
        ('coursenature', ('courseLabelId', 'courseLabelName'), (1, '必修')),
        ('faculty', ('faculty', 'facultyI18n'), ('fudan', '复旦大学')),
        ('language', ('teachingLanguage', 'teachingLanguageI18n'), ('zh', '中文')),
    ]:
        ins.cursor.execute(
            f"INSERT IGNORE INTO {table} ({cols[0]}, {cols[1]}) VALUES (%s, %s)", vals)
    ins.db.commit()
    # 为每个 teachingClassId 插入 coursedetail
    for cid in [100, 200, 300]:
        ins.cursor.execute(
            "INSERT IGNORE INTO coursedetail (id, campus, teachingLanguage, "
            "assessmentMode, courseLabelId, faculty) "
            "VALUES (%s, 'siping', 'zh', 'exam', 1, 'fudan')", (cid,))
    ins.db.commit()
    return ins


@pytest.fixture
def teacher_list():
    """模拟的 teacherList 数据（来自上游 API）。"""
    return [
        {'id': 1, 'teachingClassId': 100, 'teacherCode': '2400162', 'teacherName': '寇宗来'},
        {'id': 2, 'teachingClassId': 100, 'teacherCode': '94431', 'teacherName': '李奕滨'},
        {'id': 3, 'teachingClassId': 200, 'teacherCode': '05217', 'teacherName': '朱延娟'},
        {'id': 4, 'teachingClassId': 200, 'teacherCode': '2400163', 'teacherName': '艾剑良'},
        {'id': 5, 'teachingClassId': 300, 'teacherCode': '05082', 'teacherName': '周茜'},
        {'id': 6, 'teachingClassId': 300, 'teacherCode': '2400160', 'teacherName': '侯体健'},
    ]


class TestInsertTeachers:
    def test_normal_complete_format(self, inserter, teacher_list):
        """标准完整格式 — 不触发补全"""
        arrange = ("朱延娟(05217),艾剑良(2400163) 星期五3-4节 [1-16] 复旦五教301\n")
        inserter.insertTeachers(teacher_list, arrange)
        inserter.cursor.execute(
            "SELECT teacherName, arrangeInfoText FROM teacher WHERE teacherCode='05217'"
        )
        row = inserter.cursor.fetchone()
        assert row[0] == '朱延娟'
        assert '朱延娟(05217)' in row[1]

    def test_fudan_missing_name(self, inserter, teacher_list):
        """复旦格式：只有工号没有姓名 → 全局补全"""
        arrange = ("(2400162),李奕滨(94431) 星期三10-11节 [1-16] 复旦三教208\n"
                   "(2400162),李奕滨(94431) 星期五10-11节 [2-15] 复旦三教208\n")
        inserter.insertTeachers(teacher_list, arrange)
        # 寇宗来的记录
        inserter.cursor.execute(
            "SELECT arrangeInfoText FROM teacher WHERE teacherCode='2400162'"
        )
        kou = inserter.cursor.fetchone()[0]
        assert '寇宗来(2400162)' in kou
        assert '(2400162)' not in kou.replace('寇宗来(2400162)', '')  # 无残留裸工号
        # 李奕滨的记录也应该被补全
        inserter.cursor.execute(
            "SELECT arrangeInfoText FROM teacher WHERE teacherCode='94431'"
        )
        li = inserter.cursor.fetchone()[0]
        assert '寇宗来(2400162)' in li  # 全局补全对所有人有效

    def test_missing_code_has_name(self, inserter, teacher_list):
        """只有姓名没有工号 → 补全工号"""
        arrange = ("周茜 星期三7-8节 [1-16] 复旦光华楼西辅楼103\n")
        inserter.insertTeachers(teacher_list, arrange)
        inserter.cursor.execute(
            "SELECT arrangeInfoText FROM teacher WHERE teacherCode='05082'"
        )
        row = inserter.cursor.fetchone()[0]
        assert '周茜(05082)' in row

    def test_empty_arrange_skips(self, inserter, teacher_list):
        """空 arrangeInfo 不崩溃"""
        inserter.insertTeachers(teacher_list, '')
        inserter.cursor.execute("SELECT COUNT(*) FROM teacher")
        assert inserter.cursor.fetchone()[0] == 6  # 每人一条，schedule 为空

    def test_warn_callback(self, inserter, teacher_list):
        """warn 回调在补全时被调用"""
        warnings = []

        def capture(msg):
            warnings.append(msg)

        arrange = ("(2400162),李奕滨(94431) 星期三10-11节 [1-16] 复旦三教208\n")
        inserter.insertTeachers(teacher_list, arrange, warn=capture)
        assert len(warnings) >= 1
        assert '寇宗来' in warnings[0]
