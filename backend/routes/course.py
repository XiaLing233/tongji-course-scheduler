import json
from datetime import datetime

from flask import Blueprint, request

from bckndSql import bckndSql
from utils.bckndTools import arrangementTextToObj, splitEndline, optCourseQueryListGenerator
from utils.response import ok, err
from utils.redis_cache import cache_get, cache_set, cache_key

course_bp = Blueprint('course', __name__)


# ================================================================
#  GET /api/calendars/<id>/courses  — 课程查询（多种查询参数组合）
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/courses', methods=['GET'])
def query_courses(calendar_id):
    '''
    根据查询参数查询课程，支持三种模式：
    1. 按专业查: ?grade=2023&major=10054
    2. 按课程性质查: ?natureIds=958,957
    3. 按时段查: ?day=1&section=1
    '''
    grade = request.args.get('grade', type=int)
    major = request.args.get('major')
    nature_ids_str = request.args.get('natureIds')
    day = request.args.get('day', type=int)
    section = request.args.get('section', type=int)

    # 模式 3: 按时段查询 — normal 策略（组合太多，热度分散）
    if day is not None and section is not None:
        ck = cache_key(calendar_id, 'courses:time', day=day, section=section)
        cached = cache_get(ck)
        if cached is not None:
            return ok(cached)

        query_str = optCourseQueryListGenerator(day, section, calendar_id)
        if query_str is None:
            return err(400, "输入参数有误")
        with bckndSql(calendar_id=calendar_id) as sql:
            result = sql.findCourseByTime(query_str)

        cache_set(ck, result, 'normal')
        return ok(result)

    # 模式 2: 按课程性质查询 — static 策略
    if nature_ids_str:
        try:
            ids = tuple(int(x.strip()) for x in nature_ids_str.split(',') if x.strip())
        except ValueError:
            return err(400, "natureIds 格式错误，应为逗号分隔的数字")
        if not ids:
            return err(400, "natureIds 不能为空")

        ck = cache_key(calendar_id, 'courses:nature', ids=ids)
        cached = cache_get(ck)
        if cached is not None:
            return ok(cached)

        with bckndSql(calendar_id=calendar_id) as sql:
            try:
                result = sql.findCourseByNatureId(ids)
            except ValueError as e:
                return err(400, str(e))

        cache_set(ck, result, 'static')
        return ok(result)

    # 模式 1: 按专业查询 — hot 策略
    if grade is not None and major:
        ck = cache_key(calendar_id, 'courses:major', grade=grade, major=major)
        cached = cache_get(ck)
        if cached is not None:
            return ok(cached)

        with bckndSql(calendar_id=calendar_id) as sql:
            result = sql.findCourseByMajor(grade, major)

        # 处理 result 中的 locations 字段
        # 由于 locations 字段是一个字符串，需要转换为数组
        # 形如：关佶红(05222) 星期一3-4节 [1-17] 南129\n关佶红(05222) 星期三3-4节 [1-17单] 北301\n

        for res in result:
            for course in res['courses']:
                course['arrangementInfo'] = []
                for location in splitEndline(course['locations']):
                    course['arrangementInfo'].append(arrangementTextToObj(location))
                # 按照星期（occupyDay）和节次（occupyTime第一节）排序
                course['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))
                del course['locations']

        # 对于 code 相同的课程，合并 arrangementInfo
        for res in result:
            res['courses'] = sorted(res['courses'], key=lambda x: x['code'])  # 先排序

            # 合并相同课号的课程
            merged_courses = []
            current_course = None
            for course in res['courses']:
                if not current_course or current_course['code'] != course['code']:
                    merged_courses.append(course)
                    current_course = course
                else:
                    # 如果arrangementInfo不同，则合并（去重）
                    if current_course['arrangementInfo'] != course['arrangementInfo']:
                        # 使用字典来去重 arrangementInfo（基于 arrangementText）
                        existing_texts = {item['arrangementText'] for item in current_course['arrangementInfo']}
                        for item in course['arrangementInfo']:
                            if item['arrangementText'] not in existing_texts:
                                current_course['arrangementInfo'].append(item)
                                existing_texts.add(item['arrangementText'])
            res['courses'] = merged_courses

        cache_set(ck, result, 'hot')
        return ok(result)

    return err(400, "请提供有效的查询参数（grade+major / natureIds / day+section）")


# ================================================================
#  GET /api/calendars/<id>/course-types  — 选修课类型
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/course-types', methods=['GET'])
def get_course_types(calendar_id):
    '''
    GET /api/calendars/{id}/course-types
    获取指定学期的选修课类型。
    '''
    ck = cache_key(calendar_id, 'course-types')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findOptionalCourseType()

    cache_set(ck, result, 'static')
    return ok(result)


# ================================================================
#  POST /api/calendars/<id>/courses/details  — 批量课程详情
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/courses/details', methods=['POST'])
def batch_course_detail(calendar_id):
    '''
    POST /api/calendars/{id}/courses/details
    批量获取多个课程的详细信息。
    Payload: { "courseCodes": ["340012", "340013"] }
    '''
    payload = request.json
    codes = payload.get('courseCodes', [])

    if not codes:
        return err(400, "courseCodes 不能为空")

    codes_sorted = tuple(sorted(codes))
    ck = cache_key(calendar_id, 'courses:detail', codes=codes_sorted)
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findCourseDetailByCode(codes)

    def process(course_list):
        for course in course_list:
            course['arrangementInfo'] = []
            for location in splitEndline(course['locations']):
                course['arrangementInfo'].append(arrangementTextToObj(location))
            course['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))
            del course['locations']

        course_list = sorted(course_list, key=lambda x: x['code'])
        merged = []
        current = None
        for course in course_list:
            if not current or current['code'] != course['code']:
                merged.append(course)
                current = course
            else:
                if current['arrangementInfo'] != course['arrangementInfo']:
                    existing_texts = {item['arrangementText'] for item in current['arrangementInfo']}
                    for item in course['arrangementInfo']:
                        if item['arrangementText'] not in existing_texts:
                            current['arrangementInfo'].append(item)
                            existing_texts.add(item['arrangementText'])
        return merged

    processed = {}
    for course_code, course_list in result.items():
        processed[course_code] = process(course_list)

    cache_set(ck, processed, 'normal')
    return ok(processed)


# ================================================================
#  POST /api/calendars/<id>/courses/search  — 搜索课程
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/courses/search', methods=['POST'])
def search_courses(calendar_id):
    '''
    POST /api/calendars/{id}/courses/search
    按条件搜索课程。
    '''
    payload = request.json
    size_limit = 100

    # 用 payload 稳定 hash 做 key
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    ck = cache_key(calendar_id, 'courses:search', q=payload_str)
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result = sql.findCourseBySearch(payload, size_limit)

    data = {"courses": result, "sizeLimit": size_limit}
    cache_set(ck, data, 'normal')
    return ok(data)


# ================================================================
#  POST /api/calendars/<id>/courses/batch  — 同步用批量课程信息
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/courses/batch', methods=['POST'])
def batch_course_info(calendar_id):
    '''
    POST /api/calendars/{id}/courses/batch
    批量获取课程信息（含 isExclusive 判断，用于同步）。
    '''
    payload = request.json

    if not payload:
        return err(400, "参数错误: 缺少请求体")

    major_course_codes = payload.get('majorCourseCodes', [])
    other_course_codes = payload.get('otherCourseCodes', [])
    major_info = payload.get('majorInfo', None)

    if major_course_codes and not major_info:
        return err(400, "参数错误: majorCourseCodes 需要配合 majorInfo 使用")

    # 构建缓存 key
    codes_key = (tuple(sorted(major_course_codes)), tuple(sorted(other_course_codes)))
    grade_key = major_info.get('grade') if major_info else None
    major_key = major_info.get('code') if major_info else None
    ck = cache_key(calendar_id, 'courses:batch',
                   major=codes_key[0], other=codes_key[1],
                   grade=grade_key, major_code=major_key)
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql(calendar_id=calendar_id) as sql:
        result_dict = sql.getLatestCourseInfo(major_course_codes, other_course_codes, major_info)

        # Process arrangement info for each course code
        for course_code, course_details in result_dict.items():
            for detail in course_details:
                if 'arrangementInfo' in detail and isinstance(detail['arrangementInfo'], str):
                    # Parse arrangement text - split into list and convert each element
                    arrangement_text = detail['arrangementInfo']
                    detail['arrangementInfo'] = []
                    for location in splitEndline(arrangement_text):
                        detail['arrangementInfo'].append(arrangementTextToObj(location))

                    # Sort by day and time
                    detail['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))

            # 对于每个课程代码，合并相同 code 的课程（教学班号）
            if course_details:
                # 先按 code 排序
                course_details.sort(key=lambda x: x['code'])

                # 合并相同 code 的课程
                merged_details = []
                current_detail = None

                for detail in course_details:
                    if not current_detail or current_detail['code'] != detail['code']:
                        merged_details.append(detail)
                        current_detail = detail
                    else:
                        # 合并 arrangementInfo（去重）
                        if current_detail['arrangementInfo'] != detail['arrangementInfo']:
                            existing_texts = {item['arrangementText'] for item in current_detail['arrangementInfo']}
                            for item in detail['arrangementInfo']:
                                if item['arrangementText'] not in existing_texts:
                                    current_detail['arrangementInfo'].append(item)
                                    existing_texts.add(item['arrangementText'])

                            # 重新排序合并后的 arrangementInfo
                            current_detail['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))
                result_dict[course_code] = merged_details

    cache_set(ck, result_dict, 'normal')
    return ok(result_dict)


# ================================================================
#  GET /api/calendars/<id>/update-time  — 最新更新时间
# ================================================================

@course_bp.route('/api/calendars/<int:calendar_id>/update-time', methods=['GET'])
def get_update_time(calendar_id):
    '''
    GET /api/calendars/{id}/update-time
    获取指定学期数据的最新更新时间。
    '''
    ck = cache_key(calendar_id, 'update-time')
    cached = cache_get(ck)
    if cached is not None:
        return ok(cached)

    with bckndSql() as sql:
        result = sql.getLatestUpdateTime(calendar_id)

    data = None if result is None else datetime.strftime(result, "%Y-%m-%d %H:%M")
    cache_set(ck, data, 'static')
    return ok(data)
