from flask import Blueprint, request
from bckndSql import bckndSql
from utils.response import ok
from utils.redis_cache import cache_get, cache_set, cache_key

basic_bp = Blueprint('basic', __name__)


@basic_bp.route('/api/calendars', methods=['GET'])
def get_calendars():
    '''
    GET /api/calendars
    获取所有学期列表。
    '''
    ck = cache_key(0, 'calendars')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql() as sql:
        result = sql.getAllCalendar(limit=8)

    cache_set(ck, result, 'static')
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/campuses', methods=['GET'])
def get_campuses(calendar_id):
    '''
    GET /api/calendars/{id}/campuses
    获取指定学期的所有校区。
    '''
    ck = cache_key(calendar_id, 'campuses')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllCampus()

    cache_set(ck, result, 'static')
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/faculties', methods=['GET'])
def get_faculties(calendar_id):
    '''
    GET /api/calendars/{id}/faculties
    获取指定学期的所有院系。
    '''
    ck = cache_key(calendar_id, 'faculties')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.getAllFaculty()

    cache_set(ck, result, 'static')
    return ok(result)


@basic_bp.route('/api/calendars/<int:calendar_id>/grades', methods=['GET'])
def get_grades(calendar_id):
    '''
    GET /api/calendars/{id}/grades
    获取指定学期所有有课程的年级。
    '''
    ck = cache_key(calendar_id, 'grades')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findGrades()

    cache_set(ck, {"gradeList": result}, 'static')
    return ok({"gradeList": result})


@basic_bp.route('/api/calendars/<int:calendar_id>/grades/<int:grade>/majors', methods=['GET'])
def get_majors(calendar_id, grade):
    '''
    GET /api/calendars/{id}/grades/{grade}/majors
    获取指定学期、指定年级的所有专业。
    '''
    ck = cache_key(calendar_id, 'majors', grade=grade)
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findMajorByGrade(grade)

    cache_set(ck, result, 'static')
    return ok(result)
