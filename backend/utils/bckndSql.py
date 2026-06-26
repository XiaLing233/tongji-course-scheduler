"""Backend 只读查询。bckndSql() → 元数据库, bckndSql(calendar_id=N) → 学期库。"""

import json
import os

import mysql.connector

from .db_router import router

OPTIONAL_LABEL_LIST = [
    "通识选修课",
    "人文经典与审美素养",
    "科学探索与生命关怀",
    "社会发展与国际视野",
    "工程能力与创新思维"
]


class bckndSql:
    """只读数据库连接。calendar_id 模式走 DbRouter，否则直连元数据库。"""

    def __init__(self, calendar_id=None):
        if calendar_id is not None:
            self.db = router.get_connection(calendar_id)
        else:
            self.db = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_R_USER'),
                password=os.getenv('DB_R_PASSWORD'),
                database=os.getenv('DB_META'),
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
    #  元数据库查询
    # ================================================================

    def getAllCalendar(self, limit=8):
        self.cursor.execute(
            'SELECT JSON_OBJECT("calendarId", calendarId, "calendarName", calendarIdI18n) '
            'FROM calendar_registry '
            'WHERE calendarIdI18n != \'数据同步中…\' '
            'ORDER BY calendarId DESC LIMIT %s', (limit,)
        )
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def getLatestUpdateTime(self, calendarId=None):
        if calendarId is not None:
            self.cursor.execute(
                'SELECT startTime FROM fetchlog WHERE calendarId = %s '
                'ORDER BY startTime DESC LIMIT 1', (calendarId,)
            )
        else:
            self.cursor.execute(
                'SELECT startTime FROM fetchlog ORDER BY startTime DESC LIMIT 1'
            )
        rows = self.cursor.fetchall()
        return rows[0][0] if rows else None

    def getHealth(self):
        self.cursor.execute('SELECT 1')
        return self.cursor.fetchone()

    # ================================================================
    #  学期库查询 — 必须通过 calendar_id 连接
    # ================================================================

    def getAllCampus(self):
        self.cursor.execute(
            'SELECT JSON_OBJECT("campusId", campus, "campusName", campusI18n) FROM campus'
        )
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def getAllFaculty(self):
        self.cursor.execute(
            'SELECT JSON_OBJECT("facultyId", faculty, "facultyName", facultyI18n) FROM faculty'
        )
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def findGrades(self):
        query = (
            'SELECT DISTINCT m.grade FROM major AS m'
            ' JOIN majorandcourse AS mac ON mac.majorId = m.id'
            ' JOIN coursedetail AS c ON c.id = mac.courseId'
            ' ORDER BY m.grade DESC'
        )
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def findMajorByGrade(self, grade):
        query = (
            'SELECT JSON_OBJECT('
            " 'code', m.code,"
            " 'name', m.name"
            ' )'
            ' FROM major AS m'
            ' WHERE m.grade = %s'
            ' ORDER BY m.code ASC'
        )
        self.cursor.execute(query, (grade,))
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def findCourseByMajor(self, grade, code):
        query = """
        SELECT JSON_OBJECT(
            'courseCode', c.courseCode,
            'courseName', c.courseName,
            'faculty', f.facultyI18n,
            'credit', c.credit,
            'grade', codes.grade,
            'courseNature', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON),
            'courses', JSON_ARRAYAGG(JSON_OBJECT(
                'code', c.code,
                'teachers', teachers.teachers,
                'campus', ca.campusI18n,
                'locations', locations.locations,
                'teachingLanguage', l.teachingLanguageI18n,
                'isExclusive', IF(mac_exclusive.majorId IS NOT NULL, TRUE, FALSE) -- 判断是否存在关联的专业课程记录
            ))
        )
        FROM coursedetail as c
        JOIN faculty as f ON f.faculty = c.faculty
        JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
        JOIN campus as ca ON c.campus = ca.campus
        JOIN language as l ON l.teachingLanguage = c.teachingLanguage
        -- 获取教师信息
        JOIN (
            SELECT t.teachingClassid,
                   JSON_ARRAYAGG(JSON_OBJECT(
                       'teacherCode', t.teacherCode,
                       'teacherName', t.teacherName
                   )) AS teachers
            FROM teacher AS t GROUP BY t.teachingClassid
        ) AS teachers ON c.id = teachers.teachingClassid
        -- 获取地点信息
        JOIN (
            SELECT t.teachingClassid, t.arrangeInfoText AS locations
            FROM teacher AS t
        ) AS locations ON c.id = locations.teachingClassid
        -- 获取筛选条件和grade，并关联专业课程关系
        JOIN (
            SELECT DISTINCT c.courseCode as myCode, m.grade, m.id as targetMajorId  -- 新增：获取目标专业 ID
            FROM major AS m
            JOIN majorandcourse AS mac ON m.id = mac.majorId
            JOIN coursedetail as c ON mac.courseid = c.id
            WHERE m.grade <= %s AND m.code = %s
        ) AS codes ON c.courseCode = codes.myCode
        -- 检查是否属于专属专业（新增 LEFT JOIN）
        LEFT JOIN majorandcourse AS mac_exclusive
            ON mac_exclusive.courseid = c.id
            AND mac_exclusive.majorId = codes.targetMajorId  -- 关联目标专业 ID
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, codes.grade, c.credit
        """
        self.cursor.execute(query, (grade, code))
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def findOptionalCourseType(self):
        query = (
            f"SELECT DISTINCT n.courseLabelId, n.courseLabelName"
            f" FROM coursenature AS n"
            f" JOIN coursedetail AS c ON n.courseLabelId = c.courseLabelId"
            f" WHERE n.courseLabelName IN ({','.join(['%s'] * len(OPTIONAL_LABEL_LIST))})"
            f" ORDER BY n.courseLabelId DESC"
        )
        self.cursor.execute(query, tuple(OPTIONAL_LABEL_LIST))
        return [{"courseLabelId": r[0], "courseLabelName": r[1]} for r in self.cursor.fetchall()]

    def findCourseByNatureId(self, natureIds):
        if not natureIds:
            raise ValueError("ids 不能为空")

        # 先按当前学期和标签名范围，动态获取可查询的选修课标签 ID
        valid_query = (
            f"SELECT DISTINCT n.courseLabelId"
            f" FROM coursenature AS n JOIN coursedetail AS c ON n.courseLabelId = c.courseLabelId"
            f" WHERE n.courseLabelName IN ({','.join(['%s'] * len(OPTIONAL_LABEL_LIST))})"
        )
        self.cursor.execute(valid_query, tuple(OPTIONAL_LABEL_LIST))
        valid_ids = {row[0] for row in self.cursor.fetchall()}
        if not valid_ids:
            raise ValueError("当前学期未找到可用选修课标签")
        invalid = [nid for nid in natureIds if nid not in valid_ids]
        if invalid:
            raise ValueError(f"存在不属于当前学期选修课范围的标签 id: {', '.join(map(str, invalid))}")

        query = f"""
        SELECT JSON_OBJECT(
            'courseLabelId', courseLabelId,
            'courseLabelName', courseLabelName,
            'courses', JSON_ARRAYAGG(JSON_OBJECT(
                'courseCode', courseCode,
                'courseName', courseName,
                'faculty', facultyI18n,
                'credit', credit,
                'campus', campus_list
            ))
        )
        FROM (
            SELECT c.courseLabelId, n.courseLabelName, c.courseCode, c.courseName,
                   c.credit, f.facultyI18n,
                   CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON) AS campus_list
            FROM coursedetail as c
            JOIN faculty as f ON f.faculty = c.faculty
            JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
            JOIN campus as ca ON c.campus = ca.campus
            WHERE c.courseLabelId IN ({','.join(['%s'] * len(natureIds))})
            GROUP BY c.courseLabelId, c.courseCode, c.courseName, c.credit, f.facultyI18n    -- 按课程代码分组
        ) AS grouped_courses
        GROUP BY courseLabelId, courseLabelName
        ORDER BY courseLabelId DESC
        """
        self.cursor.execute(query, tuple(natureIds))
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def findCourseDetailByCode(self, codes):
        is_single = isinstance(codes, str)
        if is_single:
            codes = [codes]
        if not codes:
            return [] if is_single else {}

        placeholders = ','.join(['%s'] * len(codes))
        query = f"""
        SELECT c.courseCode, JSON_OBJECT(
            'code', c.code,
            'teachers', teachers.teachers,
            'campus', ca.campusI18n,
            'locations', locations.locations,
            'teachingLanguage', l.teachingLanguageI18n
        )
        FROM coursedetail as c
        JOIN campus as ca ON c.campus = ca.campus
        JOIN language as l ON l.teachingLanguage = c.teachingLanguage
        -- 获取教师信息
        JOIN (
            SELECT t.teachingClassid,
                   JSON_ARRAYAGG(JSON_OBJECT(
                       'teacherCode', t.teacherCode,
                       'teacherName', t.teacherName
                   )) AS teachers
            FROM teacher AS t GROUP BY t.teachingClassid
        ) AS teachers ON c.id = teachers.teachingClassid
        -- 获取地点信息
        JOIN (
            SELECT t.teachingClassid, t.arrangeInfoText AS locations
            FROM teacher AS t
        ) AS locations ON c.id = locations.teachingClassid
        WHERE c.courseCode IN ({placeholders})
        """
        self.cursor.execute(query, tuple(codes))
        rows = self.cursor.fetchall()

        if is_single:
            return [json.loads(row[1]) for row in rows]
        result = {c: [] for c in codes}
        for row in rows:
            cc = row[0]
            if cc in result:
                result[cc].append(json.loads(row[1]))
        return result

    def findCourseBySearch(self, searchBody, sizeLimit=50):
        params = []
        condition = ""

        if searchBody.get('courseName'):
            condition += " AND c.courseName LIKE %s"
            params.append("%" + searchBody["courseName"] + "%")
        if searchBody.get('courseCode'):
            condition += " AND (c.courseCode = %s OR c.code = %s)"
            params.extend([searchBody["courseCode"], searchBody["courseCode"]])
        if searchBody.get('teacherCode'):
            condition += " AND t.teacherCode = %s"
            params.append(searchBody["teacherCode"])
        if searchBody.get('teacherName'):
            condition += " AND t.teacherName = %s"
            params.append(searchBody["teacherName"])
        if searchBody.get('campus'):
            condition += " AND ca.campusI18n = %s"
            params.append(searchBody["campus"])
        if searchBody.get('faculty'):
            condition += " AND f.facultyI18n = %s"
            params.append(searchBody["faculty"])

        sql = f"""
        SELECT DISTINCT JSON_OBJECT(
            'courseCode', c.courseCode,
            'courseName', c.courseName,
            'faculty', f.facultyI18n,
            'credit', c.credit,
            'courseNature', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON),
            'campus', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON)
        )
        FROM coursedetail as c
        JOIN faculty AS f ON f.faculty = c.faculty
        JOIN campus as ca ON ca.campus = c.campus
        JOIN coursenature as n ON c.courseLabelId = n.courseLabelId
        JOIN teacher as t ON t.teachingClassid = c.id
        WHERE 1=1 {condition}
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, c.credit
        LIMIT %s
        """
        params.append(sizeLimit)
        self.cursor.execute(sql, tuple(params))
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def findCourseByTime(self, strSet):
        query = f"""
        SELECT JSON_OBJECT(
            'courseCode', c.courseCode,
            'courseName', c.courseName,
            'faculty', f.facultyI18n,
            'credit', c.credit,
            'courseNature', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON),
            'campus', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON)
        )
        FROM coursedetail as c
        JOIN faculty AS f ON f.faculty = c.faculty
        JOIN campus as ca ON ca.campus = c.campus
        JOIN coursenature as n ON c.courseLabelId = n.courseLabelId
        JOIN teacher as t ON t.teachingClassid = c.id
        WHERE ({' OR '.join(['t.arrangeInfoText LIKE %s'] * len(strSet))})
        AND n.courseLabelName IN ({','.join(['%s'] * len(OPTIONAL_LABEL_LIST))})
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, n.courseLabelName, c.credit
        ORDER BY courseCode ASC
        """
        self.cursor.execute(query, tuple(strSet) + tuple(OPTIONAL_LABEL_LIST))
        return [json.loads(row[0]) for row in self.cursor.fetchall()]

    def getLatestCourseInfo(self, majorCourseCodes, otherCourseCodes, majorInfo=None):
        result_dict = {}

        if majorCourseCodes and majorInfo:
            grade, code = majorInfo['grade'], majorInfo['code']
            result_dict.update({c: [] for c in majorCourseCodes})
            placeholders = ','.join(['%s'] * len(majorCourseCodes))
            query = f"""
            SELECT c.courseCode, JSON_OBJECT(
                'code', c.code,
                'teachers', teachers.teachers,
                'campusI18n', ca.campusI18n,
                'teachingLanguageI18n', l.teachingLanguageI18n,
                'arrangementInfo', locations.locations,
                'isExclusive', IF(mac_exclusive.majorId IS NOT NULL, TRUE, FALSE)
            )
            FROM coursedetail as c
            JOIN campus as ca ON c.campus = ca.campus
            JOIN language as l ON l.teachingLanguage = c.teachingLanguage
            JOIN (
                SELECT t.teachingClassid,
                       JSON_ARRAYAGG(JSON_OBJECT(
                           'teacherCode', t.teacherCode, 'teacherName', t.teacherName
                       )) as teachers
                FROM teacher as t GROUP BY t.teachingClassid
            ) as teachers ON c.id = teachers.teachingClassid
            JOIN (
                SELECT t.teachingClassid, t.arrangeInfoText as locations FROM teacher as t
            ) as locations ON c.id = locations.teachingClassid
            LEFT JOIN (
                SELECT DISTINCT c2.id as courseId, m2.id as targetMajorId
                FROM major AS m2
                JOIN majorandcourse AS mac ON m2.id = mac.majorId
                JOIN coursedetail as c2 ON mac.courseid = c2.id
                WHERE m2.grade <= %s AND m2.code = %s
            ) AS target_major ON c.id = target_major.courseId
            LEFT JOIN majorandcourse AS mac_exclusive
                ON mac_exclusive.courseid = c.id
                AND mac_exclusive.majorId = target_major.targetMajorId
            WHERE c.courseCode IN ({placeholders})
            """
            self.cursor.execute(query, (grade, code) + tuple(majorCourseCodes))
            for row in self.cursor.fetchall():
                cc = row[0]
                if cc in result_dict:
                    result_dict[cc].append(json.loads(row[1]))

        if otherCourseCodes:
            result_dict.update({c: [] for c in otherCourseCodes})
            placeholders = ','.join(['%s'] * len(otherCourseCodes))
            query = f"""
            SELECT c.courseCode, JSON_OBJECT(
                'code', c.code,
                'teachers', teachers.teachers,
                'campusI18n', ca.campusI18n,
                'teachingLanguageI18n', l.teachingLanguageI18n,
                'arrangementInfo', locations.locations
            )
            FROM coursedetail as c
            JOIN campus as ca ON c.campus = ca.campus
            JOIN language as l ON l.teachingLanguage = c.teachingLanguage
            JOIN (
                SELECT t.teachingClassid,
                       JSON_ARRAYAGG(JSON_OBJECT(
                           'teacherCode', t.teacherCode, 'teacherName', t.teacherName
                       )) as teachers
                FROM teacher as t GROUP BY t.teachingClassid
            ) as teachers ON c.id = teachers.teachingClassid
            JOIN (
                SELECT t.teachingClassid, t.arrangeInfoText as locations FROM teacher as t
            ) as locations ON c.id = locations.teachingClassid
            WHERE c.courseCode IN ({placeholders})
            """
            self.cursor.execute(query, tuple(otherCourseCodes))
            for row in self.cursor.fetchall():
                cc = row[0]
                if cc in result_dict:
                    result_dict[cc].append(json.loads(row[1]))

        return result_dict
