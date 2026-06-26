import os
from pathlib import Path

import mysql.connector
from datetime import datetime

class tjSql:
    '''MySQL 数据库操作 — 写连接。默认连元数据库，指定 database 则连学期库。'''

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

    # ================================================================
    #  维度表插入（无 calendarId — 与 course_template.sql 一致）
    # ================================================================

    def _upsert(self, table, pk_col, pk_val, cols, vals):
        """存在则跳过，不存在则插入。学期独立无需更名检测。"""
        self.cursor.execute(f"SELECT 1 FROM {table} WHERE {pk_col} = %s", (pk_val,))
        if self.cursor.fetchone() is not None:
            return
        placeholders = ', '.join(['%s'] * len(vals))
        self.cursor.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", vals
        )
        self.db.commit()

    def insertCourseLabel(self, course):
        if course.get('courseLabelId') is None:
            return
        self._upsert('coursenature', 'courseLabelId', course['courseLabelId'],
                     ['courseLabelId', 'courseLabelName'],
                     [course['courseLabelId'], course['courseLabelName']])

    def insertAssessmentMode(self, course):
        if course.get('assessmentMode') is None:
            return
        self._upsert('assessment', 'assessmentMode', course['assessmentMode'],
                     ['assessmentMode', 'assessmentModeI18n'],
                     [course['assessmentMode'], course['assessmentModeI18n']])

    def insertCampus(self, course):
        if course.get('campus') is None:
            return
        self._upsert('campus', 'campus', course['campus'],
                     ['campus', 'campusI18n'],
                     [course['campus'], course['campusI18n']])

    def insertFaculty(self, course):
        if course.get('faculty') is None:
            return
        self._upsert('faculty', 'faculty', course['faculty'],
                     ['faculty', 'facultyI18n'],
                     [course['faculty'], course['facultyI18n']])

    def insertLanguage(self, course):
        if course.get('teachingLanguage') is None:
            return
        self._upsert('language', 'teachingLanguage', course['teachingLanguage'],
                     ['teachingLanguage', 'teachingLanguageI18n'],
                     [course['teachingLanguage'], course['teachingLanguageI18n']])

    def insertMajors(self, majors):
        """
        插入专业。major 没有自然主键（PK 是 AUTO_INCREMENT id），
        所以用 SELECT + INSERT 而非 INSERT IGNORE。
        majors 格式: ['2023(10065 计算机科学与技术(图灵班))', ...]
        """
        if not majors:
            return
        for major in majors:
            code = major.split('(')[1].split(' ')[0]
            grade = major[:4]
            self.cursor.execute(
                "SELECT id FROM major WHERE code = %s AND grade = %s", (code, grade)
            )
            if self.cursor.fetchone() is not None:
                continue
            self.cursor.execute(
                "INSERT INTO major (code, grade, name) VALUES (%s, %s, %s)",
                (code, grade, major)
            )
        self.db.commit()
        self.db.commit()

    # ================================================================
    #  关联表插入（无变化）
    # ================================================================

    def insertTeachers(self, teachers, arrangeInfo):
        if not arrangeInfo:
            arrangeInfo = ''
        lines = arrangeInfo.split('\n')
        for teacher in teachers:
            schedule = ''.join(info + '\n' for info in lines if teacher['teacherName'] in info)
            self.cursor.execute(
                "INSERT INTO teacher (id, teachingClassId, teacherCode, teacherName, arrangeInfoText) "
                "VALUES (%s, %s, %s, %s, %s)",
                (teacher['id'], teacher['teachingClassId'], teacher['teacherCode'],
                 teacher['teacherName'], schedule)
            )
        self.db.commit()

    def insertMajorAndCourse(self, majors, courseId):
        if not majors:
            return
        for major in majors:
            code = major.split('(')[1].split(' ')[0]
            grade = major[:4]
            self.cursor.execute(
                "SELECT id FROM major WHERE code = %s AND grade = %s", (code, grade)
            )
            row = self.cursor.fetchone()
            if row is None:
                print(f"异常情形，专业未找到: {major}")
                continue
            self.cursor.execute(
                "INSERT INTO majorandcourse (majorId, courseId) VALUES (%s, %s)",
                (row[0], courseId)
            )
        self.db.commit()

    # ================================================================
    #  课程主表插入
    # ================================================================

    def insertCourseList(self, courses):
        """逐条插入课程 + 维度 + 关联。连接必须指向目标学期库。"""
        for course in courses:
            self.insertLanguage(course)
            self.insertCourseLabel(course)
            self.insertAssessmentMode(course)
            self.insertCampus(course)
            self.insertFaculty(course)
            self.insertMajors(course.get('majorList'))

            # 计算 newCode
            newCourseCode = course.get('newCourseCode') or ''
            newCode = None
            if newCourseCode:
                try:
                    if course.get('code') and course.get('courseCode') and course['code'].startswith(course['courseCode']):
                        newCode = newCourseCode + course['code'][-2:]
                except Exception:
                    newCode = None

            sql = (
                "INSERT INTO coursedetail ("
                "id, code, name, courseLabelId, assessmentMode, period, weekHour, "
                "campus, number, elcNumber, startWeek, endWeek, "
                "courseCode, courseName, credit, teachingLanguage, faculty, "
                "newCourseCode, newCode"
                ") VALUES ("
                "%s, %s, %s, %s, %s, %s, %s, "
                "%s, %s, %s, %s, %s, "
                "%s, %s, %s, %s, %s, "
                "%s, %s"
                ")"
            )
            val = (
                course['id'], course['code'], course['name'],
                course['courseLabelId'], course['assessmentMode'], course['period'],
                course['weekHour'], course['campus'], course['number'],
                course['elcNumber'], course['startWeek'], course['endWeek'],
                course['courseCode'], course['courseName'], course['credits'],
                course['teachingLanguage'], course['faculty'],
                newCourseCode, newCode,
            )
            try:
                self.cursor.execute(sql, val)
                self.db.commit()
            except Exception as e:
                print(e)
                print(val)
                print("\n\n\n插入数据发生异常\n\n\n")

            try:
                self.insertTeachers(course.get('teacherList'), course.get('arrangeInfo'))
            except Exception as e:
                print(f"插入教师失败: {course.get('code')} {course.get('courseName')}({course.get('name')})")
                print(f"错误: {e}")

            try:
                self.insertMajorAndCourse(course.get('majorList'), course['id'])
            except Exception as e:
                print(f"插入专业课表关联失败: {course.get('code')} {course.get('courseName')}({course.get('name')})")
                print(f"错误: {e}")

    # ================================================================
    #  US-1.1 新增：蓝绿部署 + 元数据操作
    # ================================================================

    def _use_meta(self):
        self.cursor.execute(f"USE `{os.getenv('DB_META', 'course_scheduler_meta')}`")

    def _query_active_view(self, calendarId):
        """查 active_calendars 视图，返回 (active_suffix, db_name, calendarIdI18n) 或 None。"""
        self._use_meta()
        self.cursor.execute(
            "SELECT active_suffix, db_name, calendarIdI18n FROM active_calendars WHERE calendarId = %s",
            (calendarId,)
        )
        return self.cursor.fetchone()

    def ensureCalendarDb(self, calendarId, calendarName=None):
        """
        确保学期已注册且 a/b 数据库存在，返回目标（非活跃）数据库名。
        新学期自动建库 + 注册 + GRANT。
        """
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
        return f"calendar_{calendarId}_{inactive}"

    def switchActiveDb(self, calendarId):
        """蓝绿切换。"""
        self._use_meta()
        self.cursor.execute(
            "UPDATE calendar_registry "
            "SET active_suffix = IF(active_suffix = 'a', 'b', 'a') "
            "WHERE calendarId = %s",
            (calendarId,)
        )
        self.db.commit()

    def _ensure_readonly_user(self):
        """确保只读用户存在且有权访问元数据库。"""
        r_user = os.getenv('DB_R_USER', 'readonly')
        r_pass = os.getenv('DB_R_PASSWORD', 'readonly')
        meta = os.getenv('DB_META', 'course_scheduler_meta')
        try:
            self.cursor.execute(
                f"CREATE USER IF NOT EXISTS '{r_user}'@'%%' IDENTIFIED BY %s",
                (r_pass,)
            )
            self.cursor.execute(f"GRANT SELECT ON `{meta}`.* TO '{r_user}'@'%%'")
        except mysql.connector.Error:
            pass

    def _createCalendarDbs(self, calendarId):
        """创建 calendar_{id}_a / calendar_{id}_b，执行 DDL，授权只读用户。"""
        template = (Path(__file__).resolve().parent.parent / 'course_template.sql').read_text(encoding='utf-8')
        r_user = os.getenv('DB_R_USER', 'readonly')

        self._ensure_readonly_user()

        for suffix in ('a', 'b'):
            db_name = f"calendar_{calendarId}_{suffix}"
            self.cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            self.cursor.execute(f"USE `{db_name}`")
            for stmt in template.split(';'):
                stmt = stmt.strip()
                if stmt:
                    self.cursor.execute(stmt)
            self.cursor.execute(f"GRANT SELECT ON `{db_name}`.* TO '{r_user}'@'%'")
        self.db.commit()

    def getActiveDbName(self, calendarId):
        """查询当前活跃数据库名。"""
        row = self._query_active_view(calendarId)
        return row[1] if row else None

    def calendarIdToText(self, calendarId):
        """calendarId → 学期名称。"""
        row = self._query_active_view(calendarId)
        return row[2] if row else None

    # ================================================================
    #  同步日志
    # ================================================================

    def startFetchLog(self, calendarId, msg=''):
        """开始同步：INSERT running 状态，返回 fetchlog ID。"""
        self._use_meta()
        self.cursor.execute(
            "INSERT INTO fetchlog (calendarId, startTime, status, msg) "
            "VALUES (%s, NOW(3), 'running', %s)",
            (calendarId, msg)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def finishFetchLog(self, fetchlog_id, status='completed', totalCourses=0,
                       totalPages=0, errorMessage=None, fullLog=None):
        """结束同步：UPDATE 为 completed 或 failed。"""
        self._use_meta()
        if status == 'completed':
            self.cursor.execute(
                "UPDATE fetchlog SET status='completed', endTime=NOW(3), "
                "totalCourses=%s, totalPages=%s, fullLog=%s WHERE id=%s",
                (totalCourses, totalPages, fullLog, fetchlog_id)
            )
        else:
            self.cursor.execute(
                "UPDATE fetchlog SET status='failed', endTime=NOW(3), "
                "errorMessage=%s WHERE id=%s",
                (errorMessage, fetchlog_id)
            )
        self.db.commit()

    # ================================================================
    #  结构修正工具（保留，用于临时修复）
    # ================================================================

    def updateCredits(self, course):
        self.cursor.execute("UPDATE coursedetail SET credit = %s WHERE id = %s",
                            (course['credits'], course['id']))
        self.db.commit()

    def updateLanguage(self, course):
        self.cursor.execute("UPDATE coursedetail SET teachingLanguage = %s WHERE id = %s",
                            (course['teachingLanguage'], course['id']))
        self.db.commit()
