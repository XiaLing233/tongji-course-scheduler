# API 文档

说明：所有地址遵循 RESTful 风格，资源名使用复数。`{id}` 表示 `calendarId`。

---

## API 1 获得支持的所有学期

方法：`GET`

地址：`/api/calendars`

Response：

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

说明：降序排列，确保最新的学期在第 1 个 (`data.[0]`)

---

## API 2 获得这一学期中所有的年级

方法：`GET`

地址：`/api/calendars/{id}/grades`

示例：`GET /api/calendars/119/grades`

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {
        "gradeList": [2024, 2023, 2022, 2021, 2020, 2019]
    }
}
```

说明：降序排列。

---

## API 3 获得所有的可选专业

方法：`GET`

地址：`/api/calendars/{id}/grades/{grade}/majors`

示例：`GET /api/calendars/119/grades/2023/majors`

Response：

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

说明：升序，按 code 排序。

---

## API 4 通过专业查询所有专业课

方法：`GET`

地址：`/api/calendars/{id}/courses?grade=&major=`

示例：`GET /api/calendars/119/courses?grade=2023&major=10054`

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
            "credit": 3.0,
            "grade": 2023,
            "courseNature": ["专业必修课"],
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
                }

                // ...

            ]
        }
    ]
}
```

---

## API 5 获得所有的选修课类别

方法：`GET`

地址：`/api/calendars/{id}/course-types`

示例：`GET /api/calendars/119/course-types`

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

---

## API 6 通过课程性质查询所有课程

方法：`GET`

地址：`/api/calendars/{id}/courses?natureIds=`

示例：`GET /api/calendars/119/courses?natureIds=958,957`

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
                    "campus": ["四平路校区"],
                    "courseCode": "140813",
                    "courseName": "海洋药物与健康",
                    "facultyI18n": "医学院",
                    "credit": 1.5
                }

                // ...

            ]
        },
        {
            "courseLabelId": 957,
            "courseLabelName": "社会发展与国际视野",
            "courses": [
                // ...
            ]
        }

        // ...

    ]
}
```

说明：按 `courseLabelId` 降序返回。返回的课程不包含具体的上课时间等信息，需要用 API 7 再查。

---

## API 7 通过课号获得课程的具体排课信息

方法：`POST`

地址：`/api/calendars/{id}/courses/details`

示例：`POST /api/calendars/119/courses/details`

Payload：

```json
{
    "courseCodes": ["340012", "340013", "340014"]
}
```

### Response

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": [
        {
            "code": "34001201",
            "teachers": [
                {
                    "teacherCode": "13060",
                    "teacherName": "李华"
                },
                {
                    "teacherCode": "17076",
                    "teacherName": "朱梦皎"
                }
            ],
            "campusI18n": "四平路校区",
            "arrangementInfo": [
                {
                    "arrangementText": "星期三7-8节 [2-4双 5-6 10-12 14 17] 北214\n",
                    "occupyDay": 3,
                    "occupyTime": [7, 8],
                    "occupyWeek": [2, 4, 5, 6, 10, 11, 12, 14, 17],
                    "occupyRoom": "北214"
                }
            ]
        }
    ]
}
```

说明：批量查询时返回 `{ courseCode: [...] }` 对象。

---

## API 8 高级检索课程

方法：`POST`

地址：`/api/calendars/{id}/courses/search`

示例：`POST /api/calendars/119/courses/search`

Payload：

```json
{
    "courseName": "上海",
    "courseCode": "",
    "teacherCode": "",
    "teacherName": "",
    "campus": "四平路校区",
    "faculty": ""
}
```

说明：

* 其他字段至少有一个非空。
* 关于 `courseCode`，不管是否传入二位班级序号，都可以检索。
* 返回条数上限 100 条。根据 `sizeLimit` 字段判断是否达到上限。

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
            }
        ],
        "sizeLimit": 100
    }
}
```

---

## API 9 获得所有校区

方法：`GET`

地址：`/api/calendars/{id}/campuses`

示例：`GET /api/calendars/119/campuses`

Response:

```json
{
    "code": 200,
    "data": [
        { "campusId": "1", "campusName": "四平路校区" },
        { "campusId": "3", "campusName": "嘉定校区" },
        { "campusId": "4", "campusName": "沪西校区" }
    ],
    "msg": "查询成功"
}
```

---

## API 10 获得所有学院

方法：`GET`

地址：`/api/calendars/{id}/faculties`

示例：`GET /api/calendars/119/faculties`

Response:

```json
{
    "code": 200,
    "data": [
        { "facultyId": "000034", "facultyName": "职业技术教育学院" },
        { "facultyId": "000037", "facultyName": "图书馆" },
        { "facultyId": "000039", "facultyName": "国际文化交流学院" }
    ],
    "msg": "查询成功"
}
```

---

## API 11 获得最近更新的时间

方法：`GET`

地址：`/api/calendars/{id}/update-time`

示例：`GET /api/calendars/119/update-time`

Response：

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": "2025-02-25"
}
```

---

## API 12 获得最新课程信息（同步用）

方法：`POST`

地址：`/api/calendars/{id}/courses/batch`

示例：`POST /api/calendars/119/courses/batch`

Payload:

```json
{
    "majorCourseCodes": ["340012", "100436"],
    "otherCourseCodes": ["100225"],
    "majorInfo": {
        "grade": 2022,
        "code": "1234"
    }
}
```

参数说明：

* `majorCourseCodes`：专业课程代码列表，需要返回 `isExclusive` 字段
* `otherCourseCodes`：其他课程代码列表，不返回 `isExclusive` 字段
* `majorInfo`：专业信息（`grade` + `code`），当 `majorCourseCodes` 不为空时必填

Response:

```json
{
    "code": 200,
    "msg": "查询成功",
    "data": {
        "340012": [
            {
                "code": "34001201",
                "teachers": [{ "teacherCode": "13060", "teacherName": "李华" }],
                "campusI18n": "四平路校区",
                "teachingLanguageI18n": "中文",
                "isExclusive": true,
                "arrangementInfo": [
                    {
                        "arrangementText": "星期一3-4节 [1-17] A楼101\n",
                        "occupyDay": 1,
                        "occupyTime": [3, 4],
                        "occupyWeek": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                        "occupyRoom": "A楼101"
                    }
                ]
            }
        ],
        "100225": []
    }
}
```

说明：本接口是 API 7 的批量版本，支持同步场景中一次查询多个课程的最新排课信息。如果某课程已关课，对应列表为空数组 `[]`。

---

## 同步日志 API

### 历史列表

方法：`GET`

地址：`/api/sync/history`

参数：`?calendarId=119&page=1&pageSize=20`

### 历史详情（含 fullLog）

方法：`GET`

地址：`/api/sync/history/{id}`

示例：`GET /api/sync/history/42`

### SSE 实时日志流

方法：`GET`（EventSource）

地址：`/api/sync/history/{id}/stream`

---

## 健康检查

方法：`GET`

地址：`/api/health`
