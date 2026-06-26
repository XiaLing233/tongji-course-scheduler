"""课程数据插入方法。继承 Connection，直接操作学期库。"""

from db.connection import Connection


class CourseInserter(Connection):
    """INSERT 维度表、课程表、教师、专业关联。"""

    # ---- 维度表 ----

    def _upsert(self, table, pk_col, pk_val, cols, vals):
        """存在则跳过，不存在则插入。"""
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
        """majors: ['2023(10065 计算机科学与技术(图灵班))', ...]"""
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

    # ---- 教师 & 专业关联 ----

    def insertTeachers(self, teachers, arrangeInfo):
        if not arrangeInfo:
            arrangeInfo = ''
        lines = arrangeInfo.split('\n')
        for teacher in teachers:
            schedule = ''.join(
                info + '\n' for info in lines if teacher['teacherName'] in info
            )
            self.cursor.execute(
                "INSERT INTO teacher (id, teachingClassId, teacherCode, "
                "teacherName, arrangeInfoText) VALUES (%s, %s, %s, %s, %s)",
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
                print(f"专业未找到: {major}")
                continue
            self.cursor.execute(
                "INSERT INTO majorandcourse (majorId, courseId) VALUES (%s, %s)",
                (row[0], courseId)
            )
        self.db.commit()

    # ---- 课程主表 ----

    def insertCourseList(self, courses):
        """逐条插入课程 + 维度 + 关联。连接必须指向目标学期库。"""
        for course in courses:
            self.insertLanguage(course)
            self.insertCourseLabel(course)
            self.insertAssessmentMode(course)
            self.insertCampus(course)
            self.insertFaculty(course)
            self.insertMajors(course.get('majorList'))

            newCourseCode = course.get('newCourseCode') or ''
            newCode = None
            if newCourseCode:
                try:
                    if (course.get('code') and course.get('courseCode')
                            and course['code'].startswith(course['courseCode'])):
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
