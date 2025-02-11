# Description: Table structure of the database

# assessment
ASSESSMENT_TABLE = {
    "table_name": "assessment",
    "fields": {
        "id": "assessmentMode",
        "name": "assessmentModeI18n"
    }
}

# calendar
CALENDAR_TABLE = {
    "table_name": "calendar",
    "fields": {
        "id": "calendarId",
        "name": "calendarIdI18n"
    }
}

# campus
CAMPUS_TABLE = {
    "table_name": "campus",
    "fields": {
        "id": "campus",
        "name": "campusI18n"
    }
}

#coursedetail
COURSEDETAIL_TABLE = {
    "table_name": "coursedetail",
    "fields": {
        "id": "id",
        "code": "code",
        "name": "name",
        "courseLabelId": "courseLabelId",
        "assessmentMode": "assessmentMode",
        "period": "period",
        "weekHour": "weekHour",
        "campus": "campus",
        "number": "number",
        "elcNumber": "elcNumber",
        "startWeek": "startWeek",
        "endWeek": "endWeek",
        "courseCode": "courseCode",
        "courseName": "courseName",
        "faculty": "faculty",
        "calendarId": "calendarId"
    }
}

# coursenature
COURSENATURE_TABLE = {
    "table_name": "coursenature",
    "fields": {
        "id": "courseLabelId",
        "name": "courseLabelName"
    }
}

# faculty
FACULTY_TABLE = {
    "table_name": "faculty",
    "fields": {
        "id": "faculty",
        "name": "facultyI18n"
    }
}

# major
MAJOR_TABLE = {
    "table_name": "major",
    "fields": {
        "id": "id",
        "code": "code",
        "grade": "grade",
        "name": "name",
    }
}

# majorandcourse
MAJORANDCOURSE_TABLE = {
    "table_name": "majorandcourse",
    "fields": {
        "majorId": "majorId",
        "courseId": "courseId",
    }
}

# teacher
TEACHER_TABLE = {
    "table_name": "teacher",
    "fields": {
        "id": "id",
        "teachingClassId": "teachingClassId",
        "teacherCode": "teacherCode",
        "teacherName": "teacherName",
        "arrangeInfoText": "arrangeInfoText",
    }
}