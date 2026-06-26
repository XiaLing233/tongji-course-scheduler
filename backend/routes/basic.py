from flask import Blueprint, request, jsonify
from utils import bckndSql

basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/api/getAllCalendar', methods=['GET'])
def getAllCalendar():
    '''
    Get all calendars from calendar_registry.

    Response:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
                {
                    "calendarId": 119,
                    "calendarName": "2024-2025学年第2学期"
                },
                {
                    "calendarId": 118,
                    "calendarName": "2024-2025学年第1学期"
                },

                // ...

        ]
    }
    ```
    '''
    with bckndSql.bckndSql() as sql:
        result = sql.getAllCalendar(limit=8)
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/getAllCampus', methods=['POST'])
def getAllCampus():
    '''
    Get all campuses in a calendar.

    Payload:
    ```json
    {"calendarId": 119}
    ```

    Response:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {"campusId": 3, "campusName": "嘉定校区"},
            {"campusId": 1, "campusName": "四平路校区"}
        ]
    }
    ```
    '''
    payload = request.json
    with bckndSql.bckndSql(calendar_id=payload['calendarId']) as sql:
        result = sql.getAllCampus()
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/getAllFaculty', methods=['POST'])
def getAllFaculty():
    '''
    Get all faculties in a calendar.

    Payload:
    ```json
    {"calendarId": 119}
    ```

    Response:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {
                "facultyId": 000034,
                "facultyName": "职业技术教育学院"
            },
            {
                "facultyId": 000037,
                "facultyName": "图书馆"
            },
            {
                "facultyId": 000039,
                "facultyName": "国际文化交流学院"
            },

            // ...

        ]
    }
    ```
    '''
    payload = request.json
    with bckndSql.bckndSql(calendar_id=payload['calendarId']) as sql:
        result = sql.getAllFaculty()
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/findGradeByCalendarId', methods=['POST'])
def findGradeByCalendarId():
    '''
    Find grades that have courses in a calendar.

    Payload:
    ```json
    {"calendarId": 119}
    ```

    Response:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": {
            "gradeList": [2024, 2023, 2022, 2021, 2020, 2019]
        }
    }
    ```
    '''
    payload = request.json
    with bckndSql.bckndSql(calendar_id=payload['calendarId']) as sql:
        result = sql.findGrades()
    return jsonify({"code": 200, "msg": "查询成功", "data": {"gradeList": result}}), 200


@basic_bp.route('/api/findMajorByGrade', methods=['POST'])
def findMajorByGrade():
    '''
    Find majors by grade in a calendar.

    Payload:
    ```json
    {"grade": 2023, "calendarId": 119}
    ```

    Response:
    ```json
        {
            "code": 200,
            "msg": "查询成功",
            "data": [
                {
                    "code": "00304",
                    "name": "2023(00304 基础学科拔尖基地(数学))"
                },
                {
                    "code": "00402",
                    "name": "2023(00402 基础学科拔尖基地(化学))"
                }

                // ...

            ]
        }
        ```
    '''
    payload = request.json
    with bckndSql.bckndSql(calendar_id=payload['calendarId']) as sql:
        result = sql.findMajorByGrade(payload['grade'])
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
