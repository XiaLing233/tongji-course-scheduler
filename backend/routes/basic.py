from flask import Blueprint, request, jsonify
from bckndSql import bckndSql

basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/api/calendars', methods=['GET'])
def get_calendars():
    '''
    GET /api/calendars
    获取所有学期列表。

    Response:
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {"calendarId": 119, "calendarName": "2024-2025学年第2学期"},
            ...
        ]
    }
    '''
    with bckndSql() as sql:
        result = sql.getAllCalendar(limit=8)
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/calendars/<int:calendar_id>/campuses', methods=['GET'])
def get_campuses(calendar_id):
    '''
    GET /api/calendars/{id}/campuses
    获取指定学期的所有校区。

    Response:
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {"campusId": 3, "campusName": "嘉定校区"},
            ...
        ]
    }
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllCampus()
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/calendars/<int:calendar_id>/faculties', methods=['GET'])
def get_faculties(calendar_id):
    '''
    GET /api/calendars/{id}/faculties
    获取指定学期的所有院系。

    Response:
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {"facultyId": 000034, "facultyName": "职业技术教育学院"},
            ...
        ]
    }
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllFaculty()
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200


@basic_bp.route('/api/calendars/<int:calendar_id>/grades', methods=['GET'])
def get_grades(calendar_id):
    '''
    GET /api/calendars/{id}/grades
    获取指定学期所有有课程的年级。

    Response:
    {
        "code": 200,
        "msg": "查询成功",
        "data": {"gradeList": [2024, 2023, 2022, 2021, 2020, 2019]}
    }
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findGrades()
    return jsonify({"code": 200, "msg": "查询成功", "data": {"gradeList": result}}), 200


@basic_bp.route('/api/calendars/<int:calendar_id>/grades/<int:grade>/majors', methods=['GET'])
def get_majors(calendar_id, grade):
    '''
    GET /api/calendars/{id}/grades/{grade}/majors
    获取指定学期、指定年级的所有专业。

    Response:
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {"code": "00304", "name": "2023(00304 基础学科拔尖基地(数学))"},
            ...
        ]
    }
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findMajorByGrade(grade)
    return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
