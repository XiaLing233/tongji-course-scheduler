from flask import Blueprint, request
from bckndSql import bckndSql
from utils.response import ok

basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/api/calendars', methods=['GET'])
def get_calendars():
    '''
    GET /api/calendars
    获取所有学期列表。
    '''
    with bckndSql() as sql:
        result = sql.getAllCalendar(limit=8)
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/campuses', methods=['GET'])
def get_campuses(calendar_id):
    '''
    GET /api/calendars/{id}/campuses
    获取指定学期的所有校区。
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllCampus()
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/faculties', methods=['GET'])
def get_faculties(calendar_id):
    '''
    GET /api/calendars/{id}/faculties
    获取指定学期的所有院系。
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllFaculty()
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/grades', methods=['GET'])
def get_grades(calendar_id):
    '''
    GET /api/calendars/{id}/grades
    获取指定学期所有有课程的年级。
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findGrades()
    return ok({"gradeList": result})


@basic_bp.route('/api/calendars/<int:calendar_id>/grades/<int:grade>/majors', methods=['GET'])
def get_majors(calendar_id, grade):
    '''
    GET /api/calendars/{id}/grades/{grade}/majors
    获取指定学期、指定年级的所有专业。
    '''
    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findMajorByGrade(grade)
    return ok(result)
