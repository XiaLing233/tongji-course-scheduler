import mysql.connector
import configparser
from .tjSqlTableStruct import *

# 读取配置文件
CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

# 设置数据库连接
DB_HOST = CONFIG['Sql']['host']
DB_USER = CONFIG['Sql']['user']
DB_PASSWORD = CONFIG['Sql']['password']
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

    def insertCalendar(self, course):
        '''
        Insert calendar into database
        '''
        # if exists, return
        sql = f"SELECT * FROM {CALENDAR_TABLE['table_name']} WHERE {CALENDAR_TABLE['fields']['id']} = %s"

        val = (course['calendarId'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() != None:
            return
        
        # Insert
        sql = f"INSERT INTO {CALENDAR_TABLE['table_name']} ({CALENDAR_TABLE['fields']['id']}, {CALENDAR_TABLE['fields']['name']}) VALUES (%s, %s)"

        val = (course['calendarId'], course['calendarIdI18n'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertCourseLabel(self, course):
        '''
        Insert courseLabel into database
        '''
        # if exists, return
        sql = f"SELECT * FROM {COURSENATURE_TABLE['table_name']} WHERE {COURSENATURE_TABLE['fields']['id']} = %s"

        val = (course['courseLabelId'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() != None:
            return
        
        # Insert
        sql = f"INSERT INTO {COURSENATURE_TABLE['table_name']} ({COURSENATURE_TABLE['fields']['id']}, {COURSENATURE_TABLE['fields']['name']}) VALUES (%s, %s)"

        val = (course['courseLabelId'], course['courseLabelName'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertAssessmentMode(self, course):
        '''
        Insert assessmentMode into database
        '''
        # if exists, return
        sql = f"SELECT * FROM {ASSESSMENT_TABLE['table_name']} WHERE {ASSESSMENT_TABLE['fields']['id']} = %s"

        val = (course['assessmentMode'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() != None:
            return
        
        # Insert
        sql = f"INSERT INTO {ASSESSMENT_TABLE['table_name']} ({ASSESSMENT_TABLE['fields']['id']}, {ASSESSMENT_TABLE['fields']['name']}) VALUES (%s, %s)"

        val = (course['assessmentMode'], course['assessmentModeI18n'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertCampus(self, course):
        '''
        Insert campus into database
        '''
        # if exists, return
        sql = f"SELECT * FROM {CAMPUS_TABLE['table_name']} WHERE {CAMPUS_TABLE['fields']['id']} = %s"

        val = (course['campus'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() != None:
            return
        
        # Insert
        sql = f"INSERT INTO {CAMPUS_TABLE['table_name']} ({CAMPUS_TABLE['fields']['id']}, {CAMPUS_TABLE['fields']['name']}) VALUES (%s, %s)"

        val = (course['campus'], course['campusI18n'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertFaculty(self, course):
        '''
        Insert faculty into database
        '''
        # if exists, return
        sql = f"SELECT * FROM {FACULTY_TABLE['table_name']} WHERE {FACULTY_TABLE['fields']['id']} = %s"

        val = (course['faculty'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() != None:
            return
        
        # Insert
        sql = f"INSERT INTO {FACULTY_TABLE['table_name']} ({FACULTY_TABLE['fields']['id']}, {FACULTY_TABLE['fields']['name']}) VALUES (%s, %s)"

        val = (course['faculty'], course['facultyI18n'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertMajors(self, majors):
        '''
        Insert major into database,
        majors is an array
        '''
        # if majors is empty, return
        if majors == None:
            return

        for major in majors:
            # process major
            processedMajor = {
                "code": major.split('(')[1].split(' ')[0],
                "grade": major[:4],  # first four characters of major is grade
                "name": major
            }

            # if exists, skip
            sql = f"SELECT * FROM {MAJOR_TABLE['table_name']} WHERE {MAJOR_TABLE['fields']['code']} = %s AND {MAJOR_TABLE['fields']['grade']} = %s"

            val = (processedMajor['code'], processedMajor['grade'])

            self.cursor.execute(sql, val)

            if self.cursor.fetchone() != None:
                continue

            # Insert
            sql = f"INSERT INTO {MAJOR_TABLE['table_name']} ({MAJOR_TABLE['fields']['code']}, {MAJOR_TABLE['fields']['grade']}, {MAJOR_TABLE['fields']['name']}) VALUES (%s, %s, %s)"

            val = (processedMajor['code'], processedMajor['grade'], processedMajor['name'])

            self.cursor.execute(sql, val)

        self.db.commit()

    def insertTeachers(self, teachers, arrangeInfo):
        '''
        Insert teachers into database,
        no need to check if exists,
        because schedule is unique
        '''
        # split arrangeInfo to array by '\n'
        arrangeInfo = arrangeInfo.split('\n')

        for teacher in teachers:
            # Grep arrangeInfo for this teacher
            teacherSchedule = ""
            
            for info in arrangeInfo:
                if teacher['teacherName'] in info:
                    teacherSchedule += info + '\n'
            
            # Insert teacher
            sql = f"INSERT INTO {TEACHER_TABLE['table_name']} ({TEACHER_TABLE['fields']['id']}, {TEACHER_TABLE['fields']['teachingClassId']}, {TEACHER_TABLE['fields']['teacherCode']}, {TEACHER_TABLE['fields']['teacherName']}, {TEACHER_TABLE['fields']['arrangeInfoText']}) VALUES (%s, %s, %s, %s, %s)"

            val = (teacher['id'], teacher['teachingClassId'], teacher['teacherCode'], teacher['teacherName'], teacherSchedule)

            self.cursor.execute(sql, val) 

        self.db.commit()
    
    def insertMajorAndCourse(self, majors, courseId):
        '''
        Insert major and course into database
        '''
        # if majors is empty, return
        if majors == None:
            return
        
        for major in majors:
            # Get majorId
            sql = f"SELECT {MAJOR_TABLE['fields']['id']} FROM {MAJOR_TABLE['table_name']} WHERE {MAJOR_TABLE['fields']['name']} = %s"

            val = (major, )

            self.cursor.execute(sql, val)

            majorId = self.cursor.fetchone()[0]

            # Insert
            sql = f"INSERT INTO {MAJORANDCOURSE_TABLE['table_name']} ({MAJORANDCOURSE_TABLE['fields']['majorId']}, {MAJORANDCOURSE_TABLE['fields']['courseId']}) VALUES (%s, %s)"

            val = (majorId, courseId)

            self.cursor.execute(sql, val)

        self.db.commit()

    def insertCourseList(self, courses):
        '''
        Insert course list into database
        '''
        for course in courses: # The courses array contains 20 courses
            # Handle Foreign Key Constraint First
            
            print(course)
            print("\n\n\n")
            # input()

            self.insertCourseLabel(course) # Insert courseLabel
            
            self.insertAssessmentMode(course) # Insert assessmentMode

            self.insertCampus(course) # Insert campus

            self.insertFaculty(course) # Insert faculty

            self.insertCalendar(course) # Insert calendar

            self.insertMajors(course['majorList']) # Insert major

            # print("下面要插入课程啦，按回车键继续")
            # input()

            # Insert course
            sql = (
                f"INSERT INTO {COURSEDETAIL_TABLE['table_name']} ("
                f"{COURSEDETAIL_TABLE['fields']['id']}, "
                f"{COURSEDETAIL_TABLE['fields']['code']}, "
                f"{COURSEDETAIL_TABLE['fields']['name']}, "
                f"{COURSEDETAIL_TABLE['fields']['courseLabelId']}, "
                f"{COURSEDETAIL_TABLE['fields']['assessmentMode']}, "
                f"{COURSEDETAIL_TABLE['fields']['period']}, "
                f"{COURSEDETAIL_TABLE['fields']['weekHour']}, "
                f"{COURSEDETAIL_TABLE['fields']['campus']}, "
                f"{COURSEDETAIL_TABLE['fields']['number']}, "
                f"{COURSEDETAIL_TABLE['fields']['elcNumber']}, "
                f"{COURSEDETAIL_TABLE['fields']['startWeek']}, "
                f"{COURSEDETAIL_TABLE['fields']['endWeek']}, "
                f"{COURSEDETAIL_TABLE['fields']['courseCode']}, "
                f"{COURSEDETAIL_TABLE['fields']['courseName']}, "
                f"{COURSEDETAIL_TABLE['fields']['faculty']}, "
                f"{COURSEDETAIL_TABLE['fields']['calendarId']}"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )

            val = (
                course['id'], course['code'], course['name'],
                course['courseLabelId'], course['assessmentMode'],
                course['period'], course['weekHour'], course['campus'],
                course['number'], course['elcNumber'], course['startWeek'],
                course['endWeek'], course['courseCode'], course['courseName'],
                course['faculty'], course['calendarId']
            )

            self.cursor.execute(sql, val)

            self.db.commit()

            self.insertTeachers(course['teacherList'], course['arrangeInfo']) # Insert teachers

            self.insertMajorAndCourse(course['majorList'], course['id']) # Insert major and course

        
