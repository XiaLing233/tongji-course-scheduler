import mysql.connector
import configparser

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
        sql = "SELECT * FROM calendar WHERE calendarId = %s"

        val = (course['calendarId'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO calendar (calendarId, calendarIdI18n) VALUES (%s, %s)"

        val = (course['calendarId'], course['calendarIdI18n'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertCourseLabel(self, course):
        '''
        Insert courseLabel into database
        '''
        # if none, return
        if course['courseLabelId'] is None:
            return
        
        # if exists, return
        sql = "SELECT * FROM coursenature WHERE courseLabelId = %s"

        val = (course['courseLabelId'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO coursenature (courseLabelId, courseLabelName, calendarId) VALUES (%s, %s, %s)"

        val = (course['courseLabelId'], course['courseLabelName'], course['calendarId'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertAssessmentMode(self, course):
        '''
        Insert assessmentMode into database
        '''
        # if none, return
        if course['assessmentMode'] is None:
            return
        
        # if exists, return
        sql = "SELECT * FROM assessment WHERE assessmentMode = %s"

        val = (course['assessmentMode'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO assessment (assessmentMode, assessmentModeI18n, calendarId) VALUES (%s, %s, %s)"

        val = (course['assessmentMode'], course['assessmentModeI18n'], course['calendarId'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertCampus(self, course):
        '''
        Insert campus into database
        '''
        # if none, return
        if course['campus'] is None:
            return
        
        # if exists, return
        sql = "SELECT * FROM campus WHERE campus = %s"

        val = (course['campus'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO campus (campus, campusI18n, calendarId) VALUES (%s, %s, %s)"

        val = (course['campus'], course['campusI18n'], course['calendarId'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertFaculty(self, course):
        '''
        Insert faculty into database
        '''
        # if exists, return
        sql = "SELECT * FROM faculty WHERE faculty = %s"

        val = (course['faculty'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO faculty (faculty, facultyI18n, calendarId) VALUES (%s, %s, %s)"

        val = (course['faculty'], course['facultyI18n'], course['calendarId'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertMajors(self, majors, calendarId):
        '''
        Insert major into database,
        majors is an array
        calendarId: the calendarId when this major first appears
        '''
        # if majors is empty, return
        if majors is None:
            return

        for major in majors:
            # process major
            processedMajor = {
                "code": major.split('(')[1].split(' ')[0],
                "grade": major[:4],  # first four characters of major is grade
                "name": major
            }

            # Check if exists, if exists, keep the existing calendarId (earliest one)
            sql = "SELECT * FROM major WHERE code = %s AND grade = %s"

            val = (processedMajor['code'], processedMajor['grade'])

            self.cursor.execute(sql, val)

            if self.cursor.fetchone() is not None:
                continue

            # Insert with calendarId
            sql = "INSERT INTO major (code, grade, name, calendarId) VALUES (%s, %s, %s, %s)"

            val = (processedMajor['code'], processedMajor['grade'], processedMajor['name'], calendarId)

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
            sql = "INSERT INTO teacher (id, teachingClassId, teacherCode, teacherName, arrangeInfoText) VALUES (%s, %s, %s, %s, %s)"

            val = (teacher['id'], teacher['teachingClassId'], teacher['teacherCode'], teacher['teacherName'], teacherSchedule)

            self.cursor.execute(sql, val) 

        self.db.commit()
    
    def insertMajorAndCourse(self, majors, courseId):
        '''
        Insert major and course into database
        '''
        # if majors is empty, return
        if majors is None:
            return
        
        for major in majors:
            # Get majorId
            sql = "SELECT id FROM major WHERE name = %s"

            val = (major, )

            self.cursor.execute(sql, val)

            majorId = self.cursor.fetchone()[0]

            # Insert
            sql = "INSERT INTO majorandcourse (majorId, courseId) VALUES (%s, %s)"

            val = (majorId, courseId)

            self.cursor.execute(sql, val)

        self.db.commit()

    def insertLanguage(self, course):
        '''
        Insert language into database
        '''
        # if exists, return
        sql = "SELECT * FROM language WHERE teachingLanguage = %s"

        val = (course['teachingLanguage'], )

        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return
        
        # Insert
        sql = "INSERT INTO language (teachingLanguage, teachingLanguageI18n, calendarId) VALUES (%s, %s, %s)"

        val = (course['teachingLanguage'], course['teachingLanguageI18n'], course['calendarId'])

        self.cursor.execute(sql, val)

        self.db.commit()

    def insertCourseList(self, courses):
        '''
        Insert course list into database
        '''
        for course in courses: # The courses array contains 20 courses
            # Handle Foreign Key Constraint First
            
            # print(course)
            # print("\n\n\n")
            # input()

            self.insertCalendar(course) # Insert calendar

            self.insertLanguage(course) # Insert language
            
            self.insertCourseLabel(course) # Insert courseLabel
            
            self.insertAssessmentMode(course) # Insert assessmentMode

            self.insertCampus(course) # Insert campus

            self.insertFaculty(course) # Insert faculty

            self.insertMajors(course['majorList'], course['calendarId']) # Insert major

            # print("下面要插入课程啦，按回车键继续")
            # input()

            # Calculate newCode: newCourseCode + (code - courseCode)
            newCourseCode = course.get('newCourseCode', None)
            newCode = None
            if newCourseCode is not None and newCourseCode != '':
                try:
                    # Extract the last 2 digits from code
                    codeSuffix = course['code'][-2:] if course.get('code') and course.get('courseCode') and course['code'].startswith(course['courseCode']) else ''
                    newCode = newCourseCode + codeSuffix if codeSuffix else None
                except:
                    newCode = None

            # Insert course
            sql = (
                "INSERT INTO coursedetail ("
                "id, "
                "code, "
                "name, "
                "courseLabelId, "
                "assessmentMode, "
                "period, "
                "weekHour, "
                "campus, "
                "number, "
                "elcNumber, "
                "startWeek, "
                "endWeek, "
                "courseCode, "
                "courseName, "
                "credit, "
                "teachingLanguage, "
                "faculty, "
                "calendarId, "
                "newCourseCode, "
                "newCode"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )

            val = (
                course['id'], course['code'], course['name'],
                course['courseLabelId'], course['assessmentMode'], course['period'], 
                course['weekHour'], course['campus'], course['number'], 
                course['elcNumber'], course['startWeek'], course['endWeek'], 
                course['courseCode'], course['courseName'], course['credits'],
                course['teachingLanguage'], course['faculty'], course['calendarId'],
                newCourseCode, newCode
            )

            try:
                self.cursor.execute(sql, val)

                self.db.commit()
            except Exception as e:
                print(e)
                print(val)
                print("\n\n\n插入数据发生异常\n\n\n")
                # input()

            try:
                self.insertTeachers(course['teacherList'], course['arrangeInfo']) # Insert teachers
                self.insertMajorAndCourse(course['majorList'], course['id']) # Insert major and course
            except Exception as e:
                print(e)
                print("\n\n\n插入教师数据发生异常\n\n\n")
                # input()

    def deleteOldRecordsInRange(self, currentCalendarId, depth):
        '''
        Delete records in the range of [currentCalendarId - depth + 1, currentCalendarId]
        Returns the list of calendarIds that will be deleted
        If depth is 0, no records will be deleted
        '''
        # If depth is 0, don't delete anything
        if depth <= 0:
            print("深度为 0，不删除任何记录")
            return []
        
        # Calculate the range of calendarIds to delete
        startCalendarId = currentCalendarId - depth + 1
        endCalendarId = currentCalendarId
        
        calendarIdsToDelete = list(range(startCalendarId, endCalendarId + 1))
        
        print(f"准备删除 calendarId 范围: {calendarIdsToDelete}")
        
        # Delete records from all tables
        # The foreign key constraints will automatically cascade delete
        for calendarId in calendarIdsToDelete:
            # Delete from calendar table (will cascade to other tables)
            sql = "DELETE FROM calendar WHERE calendarId = %s"
            self.cursor.execute(sql, (calendarId,))
        
        self.db.commit()
        
        print(f"已删除 {len(calendarIdsToDelete)} 个学期的记录")
        
        return calendarIdsToDelete

    def insertFetchLog(self, latestCalendar, depth):
        '''
        Insert fetch log into database
        '''
        from datetime import datetime
        
        currentTime = datetime.now()
        msg = f"{currentTime.strftime('%Y-%m-%d %H:%M:%S')}例行更新，最新学期{latestCalendar}，深度{depth}"
        
        sql = "INSERT INTO fetchlog (fetchTime, msg) VALUES (%s, %s)"
        val = (currentTime, msg)
        
        self.cursor.execute(sql, val)
        self.db.commit()
        
        print(f"已记录日志: {msg}")

# 亡羊补牢（更新表格结构）的时候需要的函数，暂时不用

    def updateCredits(self, course):
        '''
        Update credits
        '''
        sql = "UPDATE coursedetail SET credit = %s WHERE id = %s"

        val = (course['credits'], course['id'])

        self.cursor.execute(sql, val)

        print(f"Credits updated for course {course['id']} to {course['credits']}")

        # input()

        self.db.commit()
        
    def updateLanguage(self, course):
        '''
        Update language
        '''
        sql = "UPDATE coursedetail SET teachingLanguage = %s WHERE id = %s"

        val = (course['teachingLanguage'], course['id'])

        self.cursor.execute(sql, val)

        print(f"Language updated for course {course['id']} to {course['teachingLanguage']}")

        # input()

        self.db.commit()

    def calendarIdToText(self, calendarId):
        '''
        Convert calendarId to text
        '''
        sql = "SELECT calendarIdI18n FROM calendar WHERE calendarId = %s"

        val = (calendarId, )

        self.cursor.execute(sql, val)

        result = self.cursor.fetchone()

        if result is not None:
            return result[0]
        else:
            return None