from utils import bckndSql
from utils.bckndTools import arrangementTextToObj, splitEndline, optCourseQueryListGenerator
from flask import Flask, request, jsonify
import configparser
from datetime import datetime

app = Flask(__name__)

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

IS_DEBUG = CONFIG['Switch']['debug'] # 1 / 0

# 全局变量

LABEL_LIST = [ "通识选修课", "人文经典与审美素养", "科学探索与生命关怀", "社会发展与国际视野", "工程能力与创新思维" ] # 选修课标签，写死
INNER_LABEL_LIST = [811, 829, 830, 831, 832, 855, 940, 947, 955, 956, 957, 958]

@app.route('/api/getAllCalendar', methods=['GET'])
def getAllCalendar():
    '''
    Get all calendar.

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
    
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/getAllCampus', methods=['GET'])
def getAllCampus():
    '''
    Get all campus.

    Response:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {
                "campusId": 3,
                "campusName": "嘉定校区"
            },
            {
                "campusId": 1,
                "campusName": "四平路校区"
            }
        ]
    }
    ```
    '''

    with bckndSql.bckndSql() as sql:
        result = sql.getAllCampus()

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/getAllFaculty', methods=['GET'])
def getAllFaculty():
    '''
    Get all faculty.

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

    with bckndSql.bckndSql() as sql:
        result = sql.getAllFaculty()

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/findGradeByCalendarId', methods=['POST'])
def findGradeByCalendarId():
    '''
    Find grade by calendarId.

    Payload:
    ```json
    {
        "calendarId": 119
    }
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

    with bckndSql.bckndSql() as sql:
        result = sql.findGradeByCalendarId(payload['calendarId'])

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "gradeList": result
        }
    }), 200

@app.route('/api/findMajorByGrade', methods=['POST'])
def findMajorByGrade():
    '''
    Find major by grade.

    Payload:
    ```json
    {
        "grade": 2023
    }
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

    with bckndSql.bckndSql() as sql:
        result = sql.findMajorByGrade(payload['grade'])

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/findCourseByMajor', methods=['POST'])
def findCourseByMajor():
    '''
    Find course by major.

    Payload:
    ```json
    {
        "grade": 2023,
        "code": "10054",
        "calendarId": 119
    }
    ```

    Response：
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {
                "courseCode": 102020,
                "courseName": "信息论及编码理论",
                "facultyI18n": "电子与信息工程学院",
                "grade": 2023,
                "courseNature": ["专业必修课"], // 有的课程可能存在相同课号多个性质的情况
                "courses": [
                    {
                        "code": "10202005",
                        "campus": "嘉定校区",
                        "teachers": [
                            {
                                "teacherCode": "06019",
                                "teacherName": "万国春"
                            }
                        ],
                        "arrangementInfo": [
                            {
                                "arrangementText": "星期四10-12节 [1-17] 安楼A205\n",
                                "occupyDay": 4,
                                "occupyTime": [10, 11, 12],
                                "occupyWeek": [
                                    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
                                ],
                                "occupyRoom": "安楼A205"
                            }
                        ],
                        "isExclusive": 0
                    },
                    {
                        "code": "10202002",
                        "campus": "嘉定校区",
                        "teachers": [
                            {
                                "teacherCode": "00111",
                                "teacherName": "李宏强"
                            },
                            {
                                "teacherCode": "16509",
                                "teacherName": "武超"
                            }
                        ],
                        "arrangementInfo": [
                            {
                                "arrangementText": "星期一5-6节 [1-2] 安楼A304\n",
                                "occupyDay": 1,
                                "occupyTime": [5, 6],
                                "occupyWeek": [
                                    1, 2
                                ],
                                "occupyRoom": "安楼A304"
                            },
                            {
                                "arrangementText": "星期一5-6节 [3-17] 安楼A304\n",
                                "occupyDay": 1,
                                "occupyTime": [5, 6],
                                "occupyWeek": [
                                    3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17
                                ],
                                "occupyRoom": "安楼A304"
                            },
                            {
                                "arrangementText": "星期四3-4节 [1] 安楼A304\n",
                                "occupyDay": 4,
                                "occupyTime": [3, 4],
                                "occupyWeek": [
                                    1
                                ],
                                "occupyRoom": "安楼A304"
                            },
                            {
                                "arrangementText": "星期四3-4节 [3-17单] 安楼A304\n",
                                "occupyDay": 4,
                                "occupyTime": [3, 4],
                                "occupyWeek": [
                                    3, 5, 7, 9, 11, 13, 15, 17
                                ],
                                "occupyRoom": "安楼A304"
                            }
                        ],
                        "isExclusive": 1
                    },

                    // ...

                ]
            }
        ]
    }
    ```
    '''

    payload = request.json

    with bckndSql.bckndSql() as sql:
        result = sql.findCourseByMajor(payload['grade'], payload['code'], payload['calendarId'])

    # 处理 result 中的 locations 字段
    # 由于 locations 字段是一个字符串，需要转换为数组
    # 形如：关佶红(05222) 星期一3-4节 [1-17] 南129\n关佶红(05222) 星期三3-4节 [1-17单] 北301\n

    for res in result:
        for course in res['courses']:
            course['arrangementInfo'] = []
            # 使用 dict.fromkeys() 去重并保持顺序
            unique_locations = list(dict.fromkeys(splitEndline(course['locations'])))

            for location in unique_locations:
                course['arrangementInfo'].append(arrangementTextToObj(location))

            # 按照星期（occupyDay）和节次（occupyTime第一节）排序
            course['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))

            del course['locations']

    # 对于 code 相同的课程，合并 arrangementInfo

    for res in result:
        res['courses'] = sorted(res['courses'], key=lambda x: x['code']) # 先排序

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

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/findOptionalCourseType', methods=['POST'])
def findOptionalCourseType():
    '''
    Find optional course type.

    Payload

    ```json
    {
        "calendarId": 119
    }
    ```

    Response：

    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {
                "courseLabelId": 958,
                "courseLabelName": "科学探索与生命关怀"
            },
            {
                "courseLabelId": 957,
                "courseLabelName": "社会发展与国际视野"
            },
            {
                "courseLabelId": 956,
                "courseLabelName": "工程能力与创新思维"
            },
            {
                "courseLabelId": 955,
                "courseLabelName": "人文经典与审美素养"
            },
            {
                "courseLabelId": 947,
                "courseLabelName": "通识选修课"
            }
        ]
    }
    ```
    '''

    payload = request.json

    with bckndSql.bckndSql() as sql:
        result = sql.findOptionalCourseType(LABEL_LIST, payload['calendarId'])

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/findCourseByNatureId', methods=['POST'])
def findCourseByNatureId():
    '''
    Find course by nature id.

    Payload：

    ```json
    {
        "ids": [958, 957, 956, 955, 947],
        "calendarId": 119
    }
    ```

    Response：

    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [
            {
                "courseLabelId": 958,
                "courseLabelName": "科学探索与生命关怀",
                "courses": [
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140813",
                        "courseName": "海洋药物与健康",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140662",
                        "courseName": "五彩缤纷的发光材料",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140572",
                        "courseName": "人体生理学通识",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140496",
                        "courseName": "食品与健康",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140495",
                        "courseName": "食品安全导论",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "四平路校区"
                        ],
                        "courseCode": "140076",
                        "courseName": "公共营养学",
                        "facultyI18n": "医学院"
                    },
                    {
                        "campus": [
                            "嘉定校区",
                            "四平路校区"
                        ],
                        "courseCode": "124120",
                        "courseName": "物理现象探索",
                        "facultyI18n": "物理科学与工程学院"
                    }

                    // ...

                ]
            },
            {
                "courseLabelId": 957,
                "courseLabelName": "社会发展与国际视野",
                "courses": {[
                    // ...
                ]}
            },

            // ...
            
        ]
    }
    ```
    '''

    payload = request.json

    if not payload['ids'] or len(payload['ids']) == 0:
        return jsonify({
            "code": 400,
            "msg": "ids 不能为空",
        }), 400

    # 字段合法性检验
    for id in payload['ids']:
        if id not in INNER_LABEL_LIST:
            return jsonify({
                "code": 400,
                "msg": "目前只支持查询选修课标签",
            }), 400

    with bckndSql.bckndSql() as sql:
        result = sql.findCourseByNatureId(payload['ids'], payload['calendarId'])

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/findCourseDetailByCode', methods=['POST'])
def findCourseDetailByCode():
    '''
    Find course detail by code(s).

    Payload for single course:
    ```json
    {
        "courseCode": "340012",
        "calendarId": 119
    }
    ```

    Payload for multiple courses:
    ```json
    {
        "courseCodes": ["340012", "340013", "340014"],
        "calendarId": 119
    }
    ```

    Response for single course:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": [{
            "code": "34001201",
            "teachers": [...],
            "campusI18n": "四平路校区",
            "arrangementInfo": [...]
        }]
    }
    ```

    Response for multiple courses:
    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": {
            "340012": [{...}],
            "340013": [{...}],
            "340014": [{...}]
        }
    }
    ```
    '''

    payload = request.json
    
    # 判断是单个课程还是多个课程
    if 'courseCodes' in payload:
        # 批量查询
        codes = payload['courseCodes']
        is_batch = True
    else:
        # 单个查询（向后兼容）
        codes = payload['courseCode']
        is_batch = False

    with bckndSql.bckndSql() as sql:
        result = sql.findCourseDetailByCode(codes, payload['calendarId'])

    def process_course_list(course_list):
        """处理单个课程列表的通用函数"""
        for course in course_list:
            course['arrangementInfo'] = []
            unique_locations = list(dict.fromkeys(splitEndline(course['locations'])))

            for location in unique_locations:
                course['arrangementInfo'].append(arrangementTextToObj(location))

            course['arrangementInfo'].sort(key=lambda x: (x['occupyDay'], x['occupyTime'][0] if x['occupyTime'] else 0))
            del course['locations']

        # 对于 code 相同的课程，合并 arrangementInfo
        course_list = sorted(course_list, key=lambda x: x['code'])
        
        merged_result = []
        current_course = None

        for course in course_list:
            if not current_course or current_course['code'] != course['code']:
                merged_result.append(course)
                current_course = course
            else:
                if current_course['arrangementInfo'] != course['arrangementInfo']:
                    existing_texts = {item['arrangementText'] for item in current_course['arrangementInfo']}
                    for item in course['arrangementInfo']:
                        if item['arrangementText'] not in existing_texts:
                            current_course['arrangementInfo'].append(item)
                            existing_texts.add(item['arrangementText'])

        return merged_result

    if is_batch:
        # 批量处理：result 是 dict {courseCode: [details]}
        processed_result = {}
        for course_code, course_list in result.items():
            processed_result[course_code] = process_course_list(course_list)
    else:
        # 单个处理：result 是 list
        processed_result = process_course_list(result)

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": processed_result
    }), 200


@app.route('/api/findCourseBySearch', methods=['POST'])
def findCourseBySearch():
    '''
    Find course by search.

    Payload：

    ```json
    {
        "calendarId": 119,
        "courseName": "上海",
        "courseCode": "",
        "teacherCode": "",
        "teacherName": "",
        "campus": "四平路校区",
        "faculty": ""
    }
    ```

    Response：

    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": {
            "courses": [
                {
                    "courseCode": "50002950031",
                    "courseName": "乡村振兴的上海图景认知",
                    "facultyI18n": "马克思主义学院",
                    "courseNature": ["社会发展与国际视野"],
                    "campus_list": ["四平路校区"]
                },
                {
                    "courseCode": "50002680134",
                    "courseName": "学讲上海话",
                    "facultyI18n": "外国语学院",
                    "courseNature": ["人文经典与审美素养"],
                    "campus_list": ["四平路校区"]
                },
                {
                    "courseCode": "50001630031",
                    "courseName": "上海城市空间认知",
                    "facultyI18n": "建筑与城市规划学院",
                    "courseNature": ["人文经典与审美素养"],
                    "campus_list": ["四平路校区"]
                }
            ],
            "sizeLimit": 50,
        }
    }
    ```
    '''

    payload = request.json

    # 字段合法性检验，要求 Payload 中 calendarId 不为空
    if not payload['calendarId']:
        return jsonify({
            "code": 400,
            "msg": "请指定 calendarId",
        }), 400
    
    # 至少有 2 个字段不为空
    # filledCnt = 0
    # for key in payload:
    #     if payload[key]:
    #         filledCnt += 1

    # if filledCnt < 2 + 1:
    #     return jsonify({
    #         "code": 400,
    #         "msg": "请至少指定两个查询条件",
    #     }), 400
        

    sizeLimit = 100

    with bckndSql.bckndSql() as sql:
        result = sql.findCourseBySearch(payload, sizeLimit)

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "courses": result,
            "sizeLimit": sizeLimit
        }
    }), 200

@app.route('/api/findCourseByTime', methods=['POST'])
def findCourseByTime():
    '''
    Find course by time.

    Payload：

    ```json
    {
        "calendarId": 119,
        "day": 1, // 1-7
        "time": 1 // 1-12
    }
    ```

    Response:

    ```json
    {
    "code": 200,
    "data": [
        {
            "campus": [
                "嘉定校区"
            ],
            "courseCode": "122117",
            "courseName": "数学建模",
            "courseNature": [
                "科学探索与生命关怀"
            ],
            "credit": 2.0,
            "faculty": "数学科学学院"
        },

        // ...

        ],
        message: "查询成功"
    }
    ```
    接口太慢了，一天 100 门课的数据量，需要 40s 左右，需要优化
    '''

    payload = request.json

    queryStr = optCourseQueryListGenerator(payload['day'], payload['section'])

    if queryStr == None:
        return jsonify({
            "code": 400,
            "msg": "输入参数有误",
            "data": []
        }), 400

    with bckndSql.bckndSql() as sql:
        result = sql.findCourseByTime(queryStr, INNER_LABEL_LIST, payload['calendarId']) # 返回的是这一天的所有课程，需要再过滤一
        print(len(result))

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result
    }), 200

@app.route('/api/getLatestUpdateTime', methods=['GET'])
def getLatestUpdateTime():
    '''
    Get latest update time.

    Response:

    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": "2025-02-25"
    }
    ```
    '''

    with bckndSql.bckndSql() as sql:
        result = sql.getLatestUpdateTime()

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": datetime.strftime(result, "%Y-%m-%d")
    }), 200

@app.route('/api/getLatestCourseInfo', methods=['POST'])
def getLatestCourseInfo():
    '''
    Get latest course information for staged courses (batch version of API 7).

    Payload:

    ```json
    {
        "courseCodes": ["340012", "100436", "100225"],
        "calendarId": 119
    }
    ```

    Response:

    ```json
    {
        "code": 200,
        "msg": "查询成功",
        "data": {
            "340012": [course details array],
            "100436": [course details array],
            "100225": []
        }
    }
    ```
    '''

    payload = request.json

    if not payload or 'calendarId' not in payload:
        return jsonify({
            "code": 400,
            "msg": "参数错误: 缺少 calendarId",
            "data": {}
        }), 400

    calendarId = payload['calendarId']
    majorCourseCodes = payload.get('majorCourseCodes', [])  # 需要返回 isExclusive 的课程
    otherCourseCodes = payload.get('otherCourseCodes', [])  # 不需要返回 isExclusive 的课程
    majorInfo = payload.get('majorInfo', None)  # { grade, code }
    
    # 如果有 majorCourseCodes 但没有 majorInfo，返回错误
    if majorCourseCodes and not majorInfo:
        return jsonify({
            "code": 400,
            "msg": "参数错误: majorCourseCodes 需要配合 majorInfo 使用",
            "data": {}
        }), 400

    with bckndSql.bckndSql() as sql:
        result_dict = sql.getLatestCourseInfo(majorCourseCodes, otherCourseCodes, calendarId, majorInfo)
        
        # Process arrangement info for each course code
        for course_code, course_details in result_dict.items():
            for detail in course_details:
                if 'arrangementInfo' in detail and isinstance(detail['arrangementInfo'], str):
                    # Parse arrangement text - split into list and convert each element
                    arrangement_text = detail['arrangementInfo']  # 先保存原始字符串
                    detail['arrangementInfo'] = []  # 清空，准备填充解析后的数据
                    unique_locations = list(dict.fromkeys(splitEndline(arrangement_text)))
                    
                    for location in unique_locations:
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

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": result_dict
    }), 200
