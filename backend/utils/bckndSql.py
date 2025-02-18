import mysql.connector
import configparser
import json

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

# 设置数据库连接
DB_HOST = CONFIG['Sql']['host']
DB_USER = CONFIG['Sql']['r_user'] # 只读用户
DB_PASSWORD = CONFIG['Sql']['r_password'] # 只读用户密码
DB_DATABASE = CONFIG['Sql']['database']
DB_PORT = int(CONFIG['Sql']['port'])
DB_CHARSET = CONFIG['Sql']['charset']

class bckndSql:
    '''
    A class for handling MySQL database
    '''
    def __init__(self):
        '''
        Initialize the database connection
        '''
        self.db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            port=DB_PORT,
            charset=DB_CHARSET  
        )
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.db.close()
    def getAllCalendar(self):
        '''
        Get all calendar data
        '''
        self.cursor.execute(f'SELECT JSON_OBJECT("calendarId", calendarId, "calendarName", calendarIdI18n) FROM calendar')

        result = self.cursor.fetchall()

        # json str result to json
        return [json.loads(calendar[0]) for calendar in result]

    def findGradeByCalendarId(self, calendarId):
        '''
        Find grade by calendarId
        '''

        query = (
        f'SELECT DISTINCT m.grade FROM major AS m'
        f' JOIN majorandcourse AS mac ON mac.majorId = m.id'
        f' JOIN coursedetail AS c ON c.id = mac.courseId'
        f' WHERE c.calendarId = %s'
        f' ORDER BY m.grade DESC')

        self.cursor.execute(query, (calendarId, ))
        
        result = self.cursor.fetchall()

        # Convert to list
        return [grade[0] for grade in result]

    def findMajorByGrade(self, grade):
        '''
        Find major by grade
        '''

        query = (
            "SELECT JSON_OBJECT("
            " 'code', m.code,"
            " 'name', m.name"
            " )"
            " FROM major AS m"
            " WHERE m.grade = %s"
            " ORDER BY m.code ASC")

        self.cursor.execute(query, (grade, ))
        
        result = self.cursor.fetchall()

        # json str result to json
        return [json.loads(major[0]) for major in result]

    
    def findCourseByMajor(self, grade, code, calendarId):
        '''
        Find course by major
        '''
        query = f"""
        SELECT
            JSON_OBJECT(
                'courseCode', c.courseCode,
                'courseName', c.courseName,
                'facultyI18n', f.facultyI18n,
                'credit', c.credit,
                'grade', codes.grade,
                'courseNature', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON),  -- 去重
                'courses',
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'code', c.code,
                            'teachers', teachers.teachers,
                            'campus', ca.campusI18n,
                            'locations', locations.locations,
                            'isExclusive', 
                                -- 判断是否存在关联的专业课程记录
                                IF(mac_exclusive.majorId IS NOT NULL, TRUE, FALSE)
                        )
                    )
            )
        FROM coursedetail as c
        JOIN faculty as f ON f.faculty = c.faculty
        JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
        JOIN campus as ca ON c.campus = ca.campus
        -- 获取教师信息
        JOIN (
            SELECT t.teachingClassid, 
                   JSON_ARRAYAGG(
                       JSON_OBJECT(
                           'teacherCode', t.teacherCode,
                           'teacherName', t.teacherName
                       )
                   ) AS teachers
            FROM teacher AS t
            GROUP BY t.teachingClassid
        ) AS teachers ON c.id = teachers.teachingClassid
        -- 获取地点信息
        JOIN (
            SELECT t.teachingClassid, 
                   t.arrangeInfoText AS locations
            FROM teacher AS t
        ) AS locations ON c.id = locations.teachingClassid
        -- 获取筛选条件和grade，并关联专业课程关系
        JOIN (
            SELECT DISTINCT 
                c.courseCode as myCode,
                m.grade,
                m.id as targetMajorId  -- 新增：获取目标专业ID
            FROM major AS m
            JOIN majorandcourse AS mac ON m.id = mac.majorId
            JOIN coursedetail as c ON mac.courseid = c.id
            WHERE 
                m.grade <= %s
                AND m.code = %s
        ) AS codes ON c.courseCode = codes.myCode
        -- 检查是否属于专属专业（新增LEFT JOIN）
        LEFT JOIN majorandcourse AS mac_exclusive 
            ON mac_exclusive.courseid = c.id 
            AND mac_exclusive.majorId = codes.targetMajorId  -- 关联目标专业ID
        WHERE c.calendarId = %s
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, codes.grade, c.credit
        ORDER BY codes.grade desc;
        """
        self.cursor.execute(query, (grade, code, calendarId))

        result = self.cursor.fetchall()
        
        result = [json.loads(course[0]) for course in result]

        return result

        
    def findOptionalCourseType(self, labelList, calendarId):
        '''
        Find optional course type
        '''

        query = (
            f"SELECT DISTINCT"
            f" n.courseLabelId,"
            f" n.courseLabelName"
            f" FROM coursenature AS n"
            f" JOIN coursedetail AS c ON n.courseLabelId = c.courseLabelId"
            f" WHERE n.courseLabelId IN ({','.join(['%s' for _ in labelList])})"
            f" AND c.calendarId = %s"
            f" ORDER BY n.courseLabelId DESC")

        self.cursor.execute(query, tuple(labelList + [calendarId]))
        
        result = self.cursor.fetchall()

        # 添加头部
        result = [{"courseLabelId": course[0], "courseLabelName": course[1]} for course in result]

        return result
    
    def findCourseByNatureId(self, natureIds, calendarId):
        '''
        Find course by natureId
        '''

        query = f"""
        SELECT
            JSON_OBJECT(
                'courseLabelId', courseLabelId,
                'courseLabelName', courseLabelName,
                'courses', JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'courseCode', courseCode,
                                'courseName', courseName,
                                'facultyI18n', facultyI18n,
                                'credit', credit,
                                'campus', campus_list
                            )
                        )
            )
        FROM (
            SELECT
                c.courseLabelId,
                n.courseLabelName,
                c.courseCode,
                c.courseName,
                c.credit,
                f.facultyI18n,
                CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON) AS campus_list  -- 去重校区列表，并按校区名排序
            FROM coursedetail as c
            JOIN faculty as f ON f.faculty = c.faculty
            JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
            JOIN campus as ca ON c.campus = ca.campus
            JOIN calendar as cal ON c.calendarId = cal.calendarId
            WHERE c.courseLabelId IN ({','.join(['%s' for _ in natureIds])})
            AND c.calendarId = %s
            GROUP BY 
                c.courseLabelId,
                c.courseCode,  -- 按课程代码分组
                c.courseName,
                c.credit,
                f.facultyI18n
        ) AS grouped_courses
        GROUP BY courseLabelId, courseLabelName
        ORDER BY courseLabelId DESC;
        """

        self.cursor.execute(query, tuple(natureIds + [calendarId]))

        result = self.cursor.fetchall()

        # json
        result = [json.loads(res[0]) for res in result]

        # 再对courses字段进行json解析
        # for res in result:
        #     print(res["courses"])
        #     res["courses"] = json.loads(res["courses"])

        return result
    
    def findCourseDetailByCode(self, code, calendarId):
        '''
        Find course detail by code
        '''
        3
        query = f"""
        SELECT
            JSON_OBJECT(
            'code', c.code,
            'teachers', teachers.teachers,
            'campusI18n', ca.campusI18n,
            'locations', locations.locations
            )
        FROM coursedetail as c
        JOIN faculty as f ON f.faculty = c.faculty
        JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
        JOIN campus as ca ON c.campus = ca.campus
        -- 获取教师信息
        JOIN (
            SELECT t.teachingClassid, 
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'teacherCode', t.teacherCode,
                        'teacherName', t.teacherName
                    )
                ) AS teachers
            FROM teacher AS t
            GROUP BY t.teachingClassid
        ) AS teachers ON c.id = teachers.teachingClassid
        -- 获取地点信息
        JOIN (
            SELECT t.teachingClassid, 
                t.arrangeInfoText AS locations
            FROM teacher AS t
        ) AS locations ON c.id = locations.teachingClassid
        WHERE c.courseCode = %s
        AND c.calendarId = %s
        ORDER BY c.code asc;
        """

        self.cursor.execute(query, (code, calendarId))

        result = self.cursor.fetchall()

        # json
        result = [json.loads(res[0]) for res in result]

        print(result)

        return result
    
    def findCourseBySearch(self, searchBody, sizeLimit=50):
        '''
        Find course by search.
        Search Body should be an object, look like this:
        ```json
        {
            "calendarId": 119,
            "courseName": "上海",
            "courseCode": "",
            "teacherCode": "",
            "teacherName": "",
            "campus": "四平路校区",
            "faculty": "",
        }
        ```
        calendarId must exist, others should appear at least once.
        But fortunately, this logic would be done by backend, so
        we don't need to worry about this here.
        '''

        condition = ""

        # Generate condition using parameterized query
        query_params = []
        condition = ""
        if (searchBody['courseName'] != ""):
            condition += " AND c.courseName LIKE %s"
            query_params.append("%" + searchBody["courseName"] + "%")
        if (searchBody['courseCode'] != ""):
            condition += " AND (c.courseCode = %s OR c.code = %s)"
            query_params.extend([searchBody["courseCode"], searchBody["courseCode"]])
        if (searchBody['teacherCode'] != ""):
            condition += " AND t.teacherCode = %s"
            query_params.append(searchBody["teacherCode"])
        if (searchBody['teacherName'] != ""):
            condition += " AND t.teacherName = %s"
            query_params.append(searchBody["teacherName"])
        if (searchBody['campus'] != ""):
            condition += " AND ca.campusI18n = %s"
            query_params.append(searchBody["campus"])
        if (searchBody['faculty'] != ""):
            condition += " AND f.facultyI18n = %s"
            query_params.append(searchBody["faculty"])
        
        sql = f"""
        SELECT
            JSON_OBJECT(
                'courseCode', c.courseCode,
                'courseName', c.courseName,
                'faculty', f.facultyI18n,
                'courseNature', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON),  -- 去重
                'campus_list', CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON) -- 去重校区列表，并按校区名排序
            )
        FROM coursedetail as c
        JOIN faculty AS f ON f.faculty = c.faculty
        JOIN campus as ca ON ca.campus = c.campus
        JOIN coursenature as n ON c.courseLabelId = n.courseLabelId
        JOIN teacher as t ON t.teachingClassid = c.id
        WHERE c.calendarId = %s
        {condition}
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, n.courseLabelName
        ORDER BY courseCode desc
        LIMIT %s;
        """
        
        query_params.insert(0, searchBody['calendarId'])
        query_params.append(sizeLimit)
        
        self.cursor.execute(sql, tuple(query_params))

        result = self.cursor.fetchall()

        # json
        result = [json.loads(res[0]) for res in result]

        return result

testObject = {
    "calendarId": 119,
    "courseName": "上海",
    "courseCode": "",
    "teacherCode": "",
    "teacherName": "",
    "campus": "",
    "faculty": "",
}

# debug
if __name__ == '__main__':
    with bckndSql() as db:
        # print(db.findCourseDetailByCode("124004", 119))
        # print(db.findCourseByMajor(2023, "10065", 119)) ok
        # print(db.findGradeByCalendarId(119))
        # print(db.findMajorByGrade(2023))
        # print(db.findCourseBySearch(testObject)) ok
        # print(db.findCourseDetailByCode("124004", 119)) ok
        print(db.findCourseByNatureId([955, 956, 957, 958, 947], 119))
        # print(db.findOptionalCourseType([955, 956, 957, 958, 947], 119))