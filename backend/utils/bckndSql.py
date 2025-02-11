import mysql.connector
import configparser

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

class tjSql:
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
        self.cursor.execute(f'SELECT * FROM calendar')
        return self.cursor.fetchall()
    def findGradeByCalendarId(self, calendarId):
        '''
        Find grade by calendarId
        '''
        self.cursor.execute(f'SELECT DISTINCT m.grade FROM major AS m'
                            f' JOIN majorandcourse AS mac ON mac.majorId = m.id'
                            f' JOIN coursedetail AS c ON c.id = mac.courseId'
                            f' WHERE c.calendarId = {calendarId}'
                            f' ORDER BY m.grade DESC')
        
        return self.cursor.fetchall()
    def findMajorByGrade(self, grade):
        '''
        Find major by grade
        '''
        self.cursor.execute(f"SELECT m.code, m.name FROM major AS m"
                            f" WHERE m.grade = {grade}")
        
        return self.cursor.fetchall()
    def findCourseByMajor(self, grade, code, calendarId):
        '''
        Find course by major
        '''
        query = f"""
        SELECT
            c.courseCode,
            c.courseName,
            f.facultyI18n,
            codes.grade,
            CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON) AS courseNature,  -- 去重
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
            ) AS courses
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
                   JSON_ARRAYAGG(t.arrangeInfoText) AS locations
            FROM teacher AS t
            GROUP BY t.teachingClassid
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
                m.grade <= {grade} 
                AND m.code = '{code}'
        ) AS codes ON c.courseCode = codes.myCode
        -- 检查是否属于专属专业（新增LEFT JOIN）
        LEFT JOIN majorandcourse AS mac_exclusive 
            ON mac_exclusive.courseid = c.id 
            AND mac_exclusive.majorId = codes.targetMajorId  -- 关联目标专业ID
        WHERE c.calendarId = {calendarId}
        GROUP BY c.courseCode, c.courseName, f.facultyI18n, codes.grade
        ORDER BY codes.grade desc;
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
        
    def findOptionalCourseType(self, labelList, calendarId):
        '''
        Find optional course type
        '''
        # Convert Array to suitable format
        labelList = str(tuple(labelList)).replace(",)", ")") # Trailing comma

        self.cursor.execute(f"SELECT DISTINCT n.courseLabelId, n.courseLabelName FROM coursenature AS n"
                            f" JOIN coursedetail AS c ON n.courseLabelId = c.courseLabelId"
                            f" WHERE n.courseLabelId IN {labelList}"
                            f" AND c.calendarId = {calendarId}"
                            f" ORDER BY n.courseLabelId DESC")
        
        return self.cursor.fetchall()
    
    def findCourseByNatureId(self, natureIds, calendarId):
        '''
        Find course by natureId
        '''

        sql = f"""
        SELECT 
            courseLabelId,
            courseLabelName,
            CONCAT(
            '[',
            GROUP_CONCAT(
                JSON_OBJECT(
                    'courseCode', courseCode,
                    'courseName', courseName,
                    'facultyI18n', facultyI18n,
                    'campus', campus_list
                )
                ORDER BY courseCode),
                ']'
                ) AS courses
        FROM (
            SELECT
                c.courseLabelId,
                n.courseLabelName,
                c.courseCode,
                c.courseName,
                f.facultyI18n,
                CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON) AS campus_list  -- 去重校区列表，并按校区名排序
            FROM coursedetail as c
            JOIN faculty as f ON f.faculty = c.faculty
            JOIN coursenature as n ON n.courseLabelId = c.courseLabelId
            JOIN campus as ca ON c.campus = ca.campus
            JOIN calendar as cal ON c.calendarId = cal.calendarId
            WHERE c.courseLabelId IN {natureIds}
            AND c.calendarId = {calendarId}
            GROUP BY 
                c.courseLabelId,
                c.courseCode,  -- 按课程代码分组
                c.courseName,
                f.facultyI18n
        ) AS grouped_courses

        GROUP BY courseLabelId, courseLabelName
        ORDER BY courseLabelId;
        """

        self.cursor.execute(sql)

        return self.cursor.fetchall()
    
    def findCourseDetailByCode(self, code, calendarId):
        '''
        Find course detail by code
        '''
        
        sql = f"""
        SELECT
            c.code,
            teachers.teachers,
            ca.campusI18n,
            locations.locations
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
                JSON_ARRAYAGG(t.arrangeInfoText) AS locations
            FROM teacher AS t
            GROUP BY t.teachingClassid
        ) AS locations ON c.id = locations.teachingClassid
        WHERE c.courseCode = '{code}'
        AND c.calendarId = {calendarId}
        ORDER BY c.code asc;
        """

        self.cursor.execute(sql)

        return self.cursor.fetchall()
    
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

        # Generate condition
        # enumerate
        if (searchBody['courseName'] != ""):
            condition += f' AND c.courseName LIKE "%{searchBody["courseName"]}%"'
        if (searchBody['courseCode'] != ""):
            condition += f' AND (c.courseCode = "{searchBody["courseCode"]}" OR c.code = "{searchBody["courseCode"]}")'
        if (searchBody['teacherCode'] != ""):
            condition += f' AND t.teacherCode = "{searchBody["teacherCode"]}"'
        if (searchBody['teacherName'] != ""):
            condition += f' AND t.teacherName = "{searchBody["teacherName"]}"'
        if (searchBody['campus'] != ""):
            condition += f' AND ca.campusI18n = "{searchBody["campus"]}"'
        if (searchBody['faculty'] != ""):
            condition += f' AND f.facultyI18n = "{searchBody["faculty"]}"'
        
        sql=f"""
        SELECT 
            c.courseCode,
            c.courseName,
            f.facultyI18n,
            CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(n.courseLabelName)), ']') AS JSON) AS courseNature,  -- 去重
            CAST(CONCAT('[', GROUP_CONCAT(DISTINCT JSON_QUOTE(ca.campusI18n) ORDER BY ca.campusI18n), ']') AS JSON) AS campus_list  -- 去重校区列表，并按校区名排序
        FROM coursedetail as c
        JOIN faculty AS f ON f.faculty = c.faculty
        JOIN campus as ca ON ca.campus = c.campus
        JOIN coursenature as n ON c.courseLabelId = n.courseLabelId
        JOIN teacher as t ON t.teachingClassid = c.id
        WHERE c.calendarId = {searchBody['calendarId']}
        {condition}
        GROUP BY c.courseCode, c.courseName, f.facultyI18n,n.courseLabelName
        ORDER BY courseCode desc
        LIMIT {sizeLimit};
        """

        self.cursor.execute(sql)

        return self.cursor.fetchall()

testObject = {
    "calendarId": 119,
    "courseName": "",
    "courseCode": "",
    "teacherCode": "06061",
    "teacherName": "",
    "campus": "",
    "faculty": "",
}

# debug
if __name__ == '__main__':
    with tjSql() as db:
        print(db.findCourseBySearch(testObject))